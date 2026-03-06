import os
import json
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Files for persistence and learning
MEMORY_FILE = os.path.join('data', 'mapping_memory.json')

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

def load_memory():
    """Loads the keyword-to-page mapping memory."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_memory(memory):
    """Saves new mappings to the persistent memory file."""
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=4)

def find_column(df, patterns):
    """Utility to find a column name in a dataframe based on multiple patterns."""
    for pattern in patterns:
        for col in df.columns:
            if pattern.lower() in str(col).lower():
                return col
    return None

def detect_aeo_query(keyword):
    """Identifies queries that are likely targeted by Answer Engines (AEO/GEO)."""
    aeo_starters = ['how', 'what', 'why', 'where', 'who', 'when', 'is', 'can', 'best', 'top', 'vs', 'reviews']
    keyword = str(keyword).lower().strip()
    return any(keyword.startswith(starter) or f" {starter} " in f" {keyword} " for starter in aeo_starters)

def map_to_money_pages_optimized(keywords, money_pages, memory):
    """Vectorized and learned mapping logic for high speed and accuracy."""
    if not money_pages:
        return ['No pages provided'] * len(keywords)

    # 1. Pre-process Money Pages (Extract significant terms)
    page_patterns = []
    for url in money_pages:
        segments = set(url.lower().replace('-', ' ').replace('_', ' ').split('/'))
        # Filter out common URL junk
        segments = {s for s in segments if len(s) > 2 and s not in ['https:', 'http:', 'www', 'com', 'in', 'html']}
        page_patterns.append((url, segments))

    results = []
    new_memory_updates = {}

    for kw in keywords:
        kw_clean = str(kw).lower().strip()
        
        # 2. Check Learning Memory First (Instant lookup)
        if kw_clean in memory:
            results.append(memory[kw_clean])
            continue

        # 3. Fuzzy Match Strategy
        kw_words = set(kw_clean.split())
        best_match = 'General / Home'
        max_score = 0

        for url, segments in page_patterns:
            # Score based on word intersection
            score = len(kw_words.intersection(segments))
            if score > max_score:
                max_score = score
                best_match = url

        results.append(best_match)
        
        # 4. Self-Learning: If confidence is high, save to memory
        if max_score >= 1:
            new_memory_updates[kw_clean] = best_match

    # Update persistent memory
    if new_memory_updates:
        memory.update(new_memory_updates)
        save_memory(memory)

    return results

def process_seo_data(gsc_df, semrush_df, campaign_type, money_pages, location_context=None, llm_keys=None):
    """Optimized SEO processing with integrated AI Mapping and Targeting."""
    # Load Memory
    memory = load_memory()
    location_context = location_context or {"city": "", "region": "", "country": ""}
    llm_keys = llm_keys or {"openai": "", "gemini": ""}
    
    # 1. Standardize and detect columns
    gsc_df.columns = [str(c).strip() for c in gsc_df.columns]
    gsc_kw_col = find_column(gsc_df, ['query', 'keyword', 'top queries']) or gsc_df.columns[0]
    gsc_vol_col = find_column(gsc_df, ['impressions', 'clicks', 'volume']) or gsc_df.columns[1]

    # 2. Filtering & Location-Aware AEO Tagging
    if not gsc_df.empty:
        # Remove 'near me' (Captured but often filtered for strategy)
        gsc_df = gsc_df[~gsc_df[gsc_kw_col].astype(str).str.contains('near me', case=False, na=False)]
        
        # Tag AEO with Location Context
        target_loc = f"{location_context.get('city', '')} {location_context.get('region', '')}".strip()
        gsc_df['AEO_Target'] = gsc_df[gsc_kw_col].apply(detect_aeo_query)

    # 3. Handle Semrush Integration
    if semrush_df is not None and not semrush_df.empty:
        semrush_df.columns = [str(c).strip() for c in semrush_df.columns]
        sem_kw_col = find_column(semrush_df, ['keyword', 'query']) or semrush_df.columns[0]
        
        # Merge on Keyword
        merged_df = pd.merge(gsc_df, semrush_df, left_on=gsc_kw_col, right_on=sem_kw_col, how='left')
    else:
        merged_df = gsc_df.copy()
        merged_df['Intent'] = 'N/A'
        merged_df['Keyword Difficulty'] = 'N/A'
        merged_df['Position'] = 'N/A'

    # 4. Advanced AI Intelligence Engine
    # Funnel Stage mapping
    if 'Intent' in merged_df.columns:
        merged_df['Funnel'] = merged_df['Intent'].fillna('N/A').apply(map_intent_to_funnel)
    else:
        # If Intent is missing (from Semrush or just GSC only), provide a default
        merged_df['Funnel'] = 'ToFU (Default)'
        merged_df['Intent'] = 'N/A' # Ensure column exists for downstream raw data export

    # Self-Learning Semantic Mapping
    all_kws = merged_df[gsc_kw_col].tolist()
    merged_df['Mapped page'] = map_to_money_pages_optimized(all_kws, money_pages, memory)

    # 5. Prepare Export Data
    raw_data = [merged_df.columns.tolist()] + merged_df.fillna('N/A').values.tolist()

    kd_col = find_column(merged_df, ['difficulty', 'kd']) or 'Keyword Difficulty'
    rank_col = find_column(merged_df, ['position', 'rank']) or 'Position'
    
    recom_df = pd.DataFrame({
        'Recommended Keywords': merged_df[gsc_kw_col],
        'Search Volume (GSC)': merged_df[gsc_vol_col],
        'Keyword Difficulty': merged_df[kd_col] if kd_col in merged_df.columns else 'N/A',
        'Funnel Stage': merged_df['Funnel'],
        'Current Rank': merged_df[rank_col] if rank_col in merged_df.columns else 'N/A',
        'AEO Optimized?': merged_df['AEO_Target'].map({True: 'YES', False: 'No'}),
        'Mapped Page': merged_df['Mapped page'],
        'Target Location': f"{location_context['city']}, {location_context['region']}, {location_context['country']}".strip(', ')
    })
    
    # Sort by Volume
    if gsc_vol_col in merged_df.columns:
        recom_df = recom_df.sort_values(by='Search Volume (GSC)', ascending=False)
    
    recom_data = [recom_df.columns.tolist()] + recom_df.fillna('N/A').values.tolist()

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
    
    # Write data in bulk
    sheets_service.spreadsheets().values().update(
        spreadsheetId=ss_id, range="'Raw Keywords'!A1",
        valueInputOption='USER_ENTERED', body={'values': raw_data}).execute()
        
    sheets_service.spreadsheets().values().update(
        spreadsheetId=ss_id, range="'Recommended Keywords & Mapping'!A1",
        valueInputOption='USER_ENTERED', body={'values': recom_data}).execute()
        
    return ss_url

def main():
    print("--- SEO-Executive: Optimized & Learning Core ---")
    campaign_type = input("Enter Type: ").strip().capitalize()
    folder_id = input("Enter Folder ID: ").strip()
    money_pages_input = input("Enter Pages: ").strip()
    money_pages = [url.strip() for url in money_pages_input.split(',')]
    
    gsc_file = input("GSC CSV: ").strip()
    semrush_file = input("Semrush CSV (Optional): ").strip()
    
    if not os.path.exists(gsc_file):
        print("Error: GSC file not found.")
        return

    gsc_df = pd.read_csv(gsc_file)
    semrush_df = pd.read_csv(semrush_file) if semrush_file and os.path.exists(semrush_file) else None
    
    raw_data, recom_data = process_seo_data(gsc_df, semrush_df, campaign_type, money_pages)
    
    print("Authenticating...")
    sheets_service, drive_service = authenticate_google_services()
    
    if sheets_service and drive_service:
        title = f"SEO Intelligence Report - {campaign_type} ({pd.Timestamp.now().strftime('%Y-%m-%d')})"
        ss_url = create_spreadsheet_in_folder(sheets_service, drive_service, folder_id, title, raw_data, recom_data)
        print(f"\nSuccess! Learning Memory Updated. Report: {ss_url}")

if __name__ == '__main__':
    main()
