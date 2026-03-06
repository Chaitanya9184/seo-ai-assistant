import os
import sys
import asyncio
import json

# Add parent directory to path so we can import from execution/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import pandas as pd
from execution.workflow_1 import process_seo_data, authenticate_google_services, create_spreadsheet_in_folder

app = FastAPI()

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store log queues by session ID
log_queues = {}

async def log_generator(session_id: str):
    """Yields log messages and triggers engine on command."""
    if session_id not in log_queues:
        log_queues[session_id] = asyncio.Queue()
    
    queue = log_queues[session_id]
    
    try:
        while True:
            try:
                # Wait for messages or heartbeat
                message = await asyncio.wait_for(queue.get(), timeout=15.0)
                
                # Check for magic START command
                if isinstance(message, dict) and message.get('command') == 'START_ENGINE':
                    data = message['payload']
                    async def run_engine():
                        try:
                            gsc_df = data['gsc_df']
                            semrush_df = data['semrush_df']
                            campaign_type = data['campaign_type']
                            pages_list = data['pages_list']
                            loc_context = data['loc_context']
                            llm_keys = data['llm_keys']
                            folder_id = data['folder_id']

                            await queue.put({"message": f"Engine linked to stream. Analyzing data...", "type": "system", "progress": 10})
                            
                            raw_data, recom_data = process_seo_data(gsc_df, semrush_df, campaign_type, pages_list, loc_context, llm_keys)
                            await queue.put({"message": "Intelligence Engine pass complete.", "type": "info", "progress": 50})
                            
                            sheets_service, drive_service = authenticate_google_services()
                            if not sheets_service or not drive_service:
                                raise Exception("Google authentication failed. Check credentials.json.")
                            
                            title = f"SEO Query Report ({pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')})"
                            ss_url = create_spreadsheet_in_folder(sheets_service, drive_service, folder_id, title, raw_data, recom_data)
                            
                            await queue.put({
                                "message": f"Workflow Complete! Report: {ss_url}", 
                                "type": "system",
                                "status": "complete",
                                "progress": 100,
                                "url": ss_url
                            })
                        except Exception as e:
                            import traceback
                            print(traceback.format_exc())
                            await queue.put({"message": f"Processing Error: {str(e)}", "type": "error", "status": "complete"})

                    # Launch engine as part of THIS loop
                    asyncio.create_task(run_engine())
                    continue # Wait for logs from run_engine
                
                # Normal log message
                yield f"data: {json.dumps(message)}\n\n"
                
                if message.get('status') == 'complete':
                    break
                    
            except asyncio.TimeoutError:
                yield ": heartbeat\n\n"
                
    finally:
        if session_id in log_queues:
            del log_queues[session_id]

@app.get("/logs/{session_id}")
async def stream_logs(session_id: str):
    return StreamingResponse(log_generator(session_id), media_type="text/event-stream")

@app.post("/run-workflow/{session_id}")
async def run_workflow(
    session_id: str,
    campaign_type: str = Form(...),
    target_city: Optional[str] = Form(None),
    target_region: Optional[str] = Form(None),
    target_country: str = Form(...),
    folder_id: str = Form(...),
    money_pages: str = Form(...),
    semrush_status: str = Form("ranking"),
    openai_key: Optional[str] = Form(None),
    gemini_key: Optional[str] = Form(None),
    gsc_csv: UploadFile = File(...),
    semrush_csv: Optional[UploadFile] = File(None)
):
    try:
        # Ensure queue exists
        if session_id not in log_queues:
            log_queues[session_id] = asyncio.Queue()
        
        queue = log_queues[session_id]
        
        # 1. Parse Data
        gsc_content = await gsc_csv.read()
        gsc_df = pd.read_csv(pd.io.common.BytesIO(gsc_content))
        
        semrush_df = None
        if semrush_csv and semrush_status != "no-ranking":
            sem_content = await semrush_csv.read()
            semrush_df = pd.read_csv(pd.io.common.BytesIO(sem_content))

        # 2. Package and Send Trigger to Log Stream
        payload = {
            "gsc_df": gsc_df,
            "semrush_df": semrush_df,
            "campaign_type": campaign_type,
            "pages_list": [p.strip() for p in money_pages.split(',')],
            "loc_context": {"city": target_city or "", "region": target_region or "", "country": target_country},
            "llm_keys": {"openai": openai_key or "", "gemini": gemini_key or ""},
            "folder_id": folder_id
        }
        
        await queue.put({"command": "START_ENGINE", "payload": payload})
        await queue.put({"message": "Workflow request received. Handing off to stream...", "type": "info", "progress": 5})
        
        return {"status": "accepted", "session_id": session_id}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
