import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def append_via_webhook(webhook_url: str, data: dict) -> bool:
    """
    Appends data to Google Sheets via Google Apps Script Web App webhook.
    This method requires no Google Cloud console API keys or JSON credentials,
    making it extremely simple to set up and run.
    """
    try:
        headers = {"Content-Type": "application/json"}
        # Send data as post payload
        response = requests.post(webhook_url, data=json.dumps(data), headers=headers, timeout=15)
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("status") == "success":
                    print(f"[Sheets Webhook] Successfully added row: {data['company']} - {data['position']}")
                    return True
                else:
                    print(f"[Sheets Webhook] Webhook returned error status: {result.get('message')}")
            except json.JSONDecodeError:
                # Sometimes Apps Script redirection issues return HTML. Let's trace it.
                print(f"[Sheets Webhook] Success or redirection response (truncated): {response.text[:200]}")
                return False
        else:
            # Print only the first 500 characters of the error message to avoid terminal flooding
            print(f"[Sheets Webhook] HTTP Error {response.status_code}: {response.text[:500]}...")
    except Exception as e:
        print(f"[Sheets Webhook] Exception occurred: {e}")
    return False

def append_via_api(credentials_file: str, spreadsheet_identifier: str, worksheet_name: str, data: dict) -> bool:
    """
    Appends data directly via Google Sheets API (gspread).
    Requires a Google Cloud service account JSON file.
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Load credentials
        creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Open the spreadsheet. Try opening by key first, then name.
        try:
            if len(spreadsheet_identifier) > 30 and not ' ' in spreadsheet_identifier:
                # Likely a spreadsheet key
                sheet = client.open_by_key(spreadsheet_identifier)
            else:
                sheet = client.open(spreadsheet_identifier)
        except Exception as e:
            print(f"[Sheets API] Error opening spreadsheet '{spreadsheet_identifier}': {e}")
            return False
            
        # Get the worksheet
        try:
            worksheet = sheet.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # Create if not exists or default to first sheet
            print(f"[Sheets API] Worksheet '{worksheet_name}' not found. Using the first worksheet.")
            worksheet = sheet.get_worksheet(0)
            
        # If the sheet is empty, add header row
        existing_records = worksheet.get_all_values()
        if not existing_records:
            headers = ["Company Name", "Position", "Qualifications", "Experience", "Location", "Apply Link", "Posted Date"]
            worksheet.append_row(headers)
            
        # Build the row
        row = [
            data.get("company", "N/A"),
            data.get("position", "N/A"),
            data.get("qualifications", "N/A"),
            data.get("experience", "N/A"),
            data.get("location", "N/A"),
            data.get("apply_link", "N/A"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        
        worksheet.append_row(row)
        print(f"[Sheets API] Successfully appended row: {data['company']} - {data['position']}")
        return True
        
    except ImportError:
        print("[Sheets API] Error: 'gspread' or 'google-auth' is not installed.")
        return False
    except Exception as e:
        print(f"[Sheets API] Exception occurred: {e}")
        return False

def add_to_sheet(data: dict) -> bool:
    """
    Main router function to add job data to Google Sheet based on configuration.
    """
    method = os.getenv("SHEET_METHOD", "webhook").lower()
    
    if method == "webhook":
        webhook_url = os.getenv("GOOGLE_SHEET_WEBHOOK_URL")
        if not webhook_url:
            print("[Sheets Router] Error: SHEET_METHOD is set to 'webhook' but GOOGLE_SHEET_WEBHOOK_URL is not configured in .env.")
            return False
        return append_via_webhook(webhook_url, data)
        
    elif method == "api":
        credentials_file = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json")
        spreadsheet = os.getenv("GOOGLE_SHEETS_SPREADSHEET", "")
        worksheet = os.getenv("GOOGLE_SHEETS_WORKSHEET", "Sheet1")
        
        if not spreadsheet:
            print("[Sheets Router] Error: SHEET_METHOD is set to 'api' but GOOGLE_SHEETS_SPREADSHEET is not configured in .env.")
            return False
            
        if not os.path.exists(credentials_file):
            print(f"[Sheets Router] Error: Google credentials file '{credentials_file}' not found.")
            return False
            
        return append_via_api(credentials_file, spreadsheet, worksheet, data)
        
    else:
        print(f"[Sheets Router] Error: Unknown SHEET_METHOD '{method}'. Choose 'webhook' or 'api'.")
        return False
