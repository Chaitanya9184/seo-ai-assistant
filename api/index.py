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

# Global queue to store logs for the current session
log_queue = asyncio.Queue()

async def log_generator():
    """Yields log messages as they are added to the queue."""
    while True:
        message = await log_queue.get()
        yield f"data: {json.dumps(message)}\n\n"
        if message.get('status') == 'complete':
            break

@app.get("/logs")
async def stream_logs():
    """Endpoint for the frontend to listen to SSE logs."""
    return StreamingResponse(log_generator(), media_type="text/event-stream")

@app.post("/run-workflow")
async def run_workflow(
    campaign_type: str = Form(...),
    folder_id: str = Form(...),
    money_pages: str = Form(...),
    semrush_status: str = Form("ranking"),
    gsc_csv: UploadFile = File(...),
    semrush_csv: Optional[UploadFile] = File(None)
):
    """Processes SEO data and triggers Workflow 1."""
    
    # Read file contents immediately into memory BEFORE returning (prevents closed file error)
    gsc_content = await gsc_csv.read()
    sem_content = await semrush_csv.read() if semrush_csv and semrush_status != "no-ranking" else None

    async def task():
        try:
            await log_queue.put({"message": f"Initializing {campaign_type} campaign workflow...", "type": "system", "progress": 5})
            
            # Save temporary files in /tmp (standard for Vercel)
            gsc_path = "/tmp/gsc_temp.csv"
            sem_path = "/tmp/semrush_temp.csv"
            
            await log_queue.put({"message": "Validating uploaded CSV assets...", "type": "info", "progress": 10})
            
            with open(gsc_path, "wb") as f:
                f.write(gsc_content)
            
            semrush_df = None
            if sem_content:
                with open(sem_path, "wb") as f:
                    f.write(sem_content)
                semrush_df = pd.read_csv(sem_path)
                await log_queue.put({"message": "GSC and Semrush datasets verified.", "type": "info", "progress": 20})
            else:
                await log_queue.put({"message": "GSC verified. Semrush data bypassed (Fresh site mode).", "type": "info", "progress": 20})
                
            # Load GSC
            await log_queue.put({"message": "Parsing Search Console data...", "type": "info", "progress": 30})
            gsc_df = pd.read_csv(gsc_path)
            pages_list = [p.strip() for p in money_pages.split(',')]
            
            await log_queue.put({"message": "Running SEO Intelligence Engine...", "type": "info", "progress": 40})
            await log_queue.put({"message": "-> Performing semantic mapping to Money Pages...", "type": "info", "progress": 50})
            await log_queue.put({"message": "-> Detecting AEO/GEO query opportunities...", "type": "info", "progress": 60})
            
            raw_data, recom_data = process_seo_data(gsc_df, semrush_df, campaign_type, pages_list)
            
            await log_queue.put({"message": "Filtering 'near me' noise and finalizing datasets...", "type": "info", "progress": 70})
            
            # Authenticate and Export
            await log_queue.put({"message": "Authenticating with Google Cloud Services...", "type": "info", "progress": 80})
            sheets_service, drive_service = authenticate_google_services()
            
            if not sheets_service or not drive_service:
                raise Exception("Google authentication failed. Check credentials.json.")
                
            title = f"SEO Query Report - {campaign_type} ({pd.Timestamp.now().strftime('%Y-%m-%d')})"
            await log_queue.put({"message": f"Creating new Google Spreadsheet in folder: {folder_id}...", "type": "info", "progress": 90})
            
            ss_url = create_spreadsheet_in_folder(sheets_service, drive_service, folder_id, title, raw_data, recom_data)
            
            await log_queue.put({
                "message": f"Workflow Complete! Access your report here: {ss_url}", 
                "type": "system",
                "status": "complete",
                "progress": 100,
                "url": ss_url
            })
            
        except Exception as e:
            await log_queue.put({"message": f"Error: {str(e)}", "type": "error", "status": "complete"})
            
    # Trigger background task
    asyncio.create_task(task())
    return {"status": "started"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
