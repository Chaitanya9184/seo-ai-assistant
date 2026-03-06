import os
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']

def authenticate_google_services():
    """Authenticates the user with Google Sheets and Drive APIs."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("Error: credentials.json not found. Please download it from Google Cloud Console.")
                return None, None
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    return sheets_service, drive_service

def map_intent_to_funnel(intent):
    """Maps Semrush intent to Funnel stages (ToFU, MoFU, BoFU)."""
    intent = str(intent).lower()
    if 'informational' in intent:
        return 'ToFU'
    elif 'navigational' in intent or 'commercial' in intent:
        return 'MoFU'
    elif 'transactional' in intent:
        return 'BoFU'
    return 'Unknown'

def process_seo_data(gsc_df, semrush_df, campaign_type, money_pages):
    """Processes and merges GSC and Semrush data based on campaign requirements."""
    # 1. Standardize column names
    # Expecting GSC columns: 'Query' and 'Clicks' or 'Impressions' (volume)
    # Expecting Semrush columns: 'Keyword', 'Keyword Difficulty', 'Intent', 'Position' (rankings)
    
    gsc_df = gsc_df.rename(columns=lambda x: x.strip())
    semrush_df = semrush_df.rename(columns=lambda x: x.strip())
    
    # 2. Filtering
    # Remove 'near me' keywords
    gsc_df = gsc_df[~gsc_df.iloc[:,0].str.contains('near me', case=False, na=False)]
    semrush_df = semrush_df[~semrush_df.iloc[:,0].str.contains('near me', case=False, na=False)]
    
    # 3. Merge Datasets (Exact Join on Keyword)
    # GSC iloc[:,0] is usually 'Query', Semrush iloc[:,0] is 'Keyword'
    merged_df = pd.merge(gsc_df, semrush_df, left_on=gsc_df.columns[0], right_on=semrush_df.columns[0], how='inner')
    
    # 4. Map Funnel
    if 'Intent' in merged_df.columns:
        merged_df['Funnel'] = merged_df['Intent'].apply(map_intent_to_funnel)
    else:
        merged_df['Funnel'] = 'Unknown'
        
    # 5. Mapping to Money Pages (Simple Placeholder for now)
    # In a real scenario, we might use NLP or URL logic.
    merged_df['Mapped page'] = 'To be mapped'
    
    # Raw Keywords Tab Data
    raw_data = [merged_df.columns.tolist()] + merged_df.values.tolist()
    
    # Recommended Keywords Tab Data (Tab 2 Schema)
    # Recomended Keywords | Search volume | Keyword difficulty | Funnel | Current rankings | Mapped page
    tab2_cols = []
    # Attempt to find columns based on expected names
    kw_col = merged_df.columns[0]
    vol_col = next((c for c in merged_df.columns if 'Impressions' in c or 'Clicks' in c or 'Volume' in c), merged_df.columns[1])
    kd_col = next((c for c in merged_df.columns if 'Difficulty' in c), 'N/A')
    rank_col = next((c for c in merged_df.columns if 'Position' in c), 'N/A')
    
    recom_df = pd.DataFrame({
        'Recomended Keywords': merged_df[kw_col],
        'Search volume': merged_df[vol_col],
        'Keyword difficulty': merged_df[kd_col] if kd_col in merged_df.columns else 'N/A',
        'Funnel': merged_df['Funnel'],
        'Current rankings': merged_df[rank_col] if rank_col in merged_df.columns else 'N/A',
        'Mapped page': merged_df['Mapped page']
    })
    
    recom_data = [recom_df.columns.tolist()] + recom_df.values.tolist()
    
    return raw_data, recom_data

def create_spreadsheet_in_folder(sheets_service, drive_service, folder_id, title, raw_data, recom_data):
    """Creates a two-tab spreadsheet in the specified Drive folder."""
    spreadsheet = {
        'properties': {'title': title},
        'sheets': [
            {'properties': {'title': 'Raw Keywords'}},
            {'properties': {'title': 'Recommended Keywords & Mapping'}}
        ]
    }
    ss = sheets_service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId,spreadsheetUrl').execute()
    ss_id = ss.get('spreadsheetId')
    ss_url = ss.get('spreadsheetUrl')
    
    # Move to folder
    file = drive_service.files().get(fileId=ss_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))
    drive_service.files().update(fileId=ss_id, addParents=folder_id, removeParents=previous_parents, fields='id, parents').execute()
    
    # Write data to Tab 1
    sheets_service.spreadsheets().values().update(
        spreadsheetId=ss_id, range="'Raw Keywords'!A1",
        valueInputOption='USER_ENTERED', body={'values': raw_data}).execute()
        
    # Write data to Tab 2
    sheets_service.spreadsheets().values().update(
        spreadsheetId=ss_id, range="'Recommended Keywords & Mapping'!A1",
        valueInputOption='USER_ENTERED', body={'values': recom_data}).execute()
        
    return ss_url

def main():
    print("--- SEO-Executive: Advanced Query Report ---")
    
    campaign_type = input("Enter Campaign Type (Local, Regional, National): ").strip().capitalize()
    folder_id = input("Enter Google Drive Folder ID: ").strip()
    money_pages_input = input("Enter Money Pages (comma separated URLs): ").strip()
    money_pages = [url.strip() for url in money_pages_input.split(',')]
    
    gsc_file = input("Path to GSC CSV: ").strip()
    semrush_file = input("Path to Semrush CSV: ").strip()
    
    if not os.path.exists(gsc_file) or not os.path.exists(semrush_file):
        print("Error: Input files not found.")
        return

    gsc_df = pd.read_csv(gsc_file)
    semrush_df = pd.read_csv(semrush_file)
    
    raw_data, recom_data = process_seo_data(gsc_df, semrush_df, campaign_type, money_pages)
    
    print("Authenticating with Google Services...")
    sheets_service, drive_service = authenticate_google_services()
    
    if sheets_service and drive_service:
        title = f"SEO Query Report - {campaign_type}"
        ss_url = create_spreadsheet_in_folder(sheets_service, drive_service, folder_id, title, raw_data, recom_data)
        print(f"\nSuccess! Spreadsheet created at: {ss_url}")

if __name__ == '__main__':
    main()
