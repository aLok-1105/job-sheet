# Telegram to Google Sheet Job Board Sync

A robust Python script that listens to one or more Telegram channels/groups, automatically parses job postings matching your target format, and adds them directly to a Google Sheet.

## Features

- **Multi-channel support**: Listen to one or multiple Telegram groups/channels.
- **Smart parsing**: Auto-extracts **Company Name**, **Position**, **Qualifications**, **Experience**, **Location**, and the **Apply Link** while ignoring promotional social links (like WhatsApp/Telegram invites).
- **Flexible Google Sheets integration**:
  - **Google Apps Script Web App** (Recommended: super fast setup, no credentials files or Cloud console required).
  - **Google Sheets API** (Standard: uses Service Account `credentials.json`).
- **Interactive login support**: Automatically logs in using your personal Telegram account (if you are a member of the group but don't own it) or as a Bot account (if you own the group).

---

## Step 1: Google Sheets Setup

Choose **one** of the two methods below to link your Google Sheet.

### Method A: Google Apps Script Web App (Recommended)
This is the simplest way. No Google Cloud APIs or JSON credential files are needed.

1. Open your Google Sheet.
2. Rename the active sheet tab to **Sheet1** (or matching your config).
3. In the top menu, click **Extensions** > **Apps Script**.
4. Replace all code in the editor with the following code:
   ```javascript
   function doPost(e) {
     try {
       var jsonString = e.postData.contents;
       var data = JSON.parse(jsonString);
       
       var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
       
       // If sheet is empty, write header columns
       if (sheet.getLastRow() === 0) {
         sheet.appendRow(["Company Name", "Position", "Qualifications", "Experience", "Location", "Apply Link", "Posted Date"]);
       }
       
       // Append the job details
       sheet.appendRow([
         data.company || "N/A",
         data.position || "N/A",
         data.qualifications || "N/A",
         data.experience || "N/A",
         data.location || "N/A",
         data.apply_link || "N/A",
         new Date().toLocaleString()
       ]);
       
       return ContentService.createTextOutput(JSON.stringify({ "status": "success", "message": "Job added successfully!" }))
                            .setMimeType(ContentService.MimeType.JSON);
     } catch (error) {
       return ContentService.createTextOutput(JSON.stringify({ "status": "error", "message": error.toString() }))
                            .setMimeType(ContentService.MimeType.JSON);
     }
   }
   ```
5. Click **Save** (floppy disk icon).
6. Click **Deploy** > **New Deployment** (top right).
7. Select type: **Web App** (click gear icon next to "Select type").
8. Configure:
   - **Description**: Job Sheet Bot Link
   - **Execute as**: **Me** (your-email@gmail.com)
   - **Who has access**: **Anyone** (this allows the python script to send data without OAuth complications)
9. Click **Deploy**. Authorize access if prompted (Google will warn that the app isn't verified; click "Advanced" and "Go to Untitled project (unsafe)" to approve).
10. **Copy the Web App URL** displayed under "Web app". You'll paste this into your `.env` file as `GOOGLE_SHEET_WEBHOOK_URL`.

---

### Method B: Google Sheets API
If you prefer direct Google Cloud Platform API access:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project, enable the **Google Sheets API** and **Google Drive API**.
3. Create a **Service Account** and download its key as a **JSON** file.
4. Rename that downloaded JSON file to `credentials.json` and place it in this project folder.
5. Open your Google Sheet and share it with the service account email (found inside `credentials.json`, ending with `.gserviceaccount.com`) as an **Editor**.
6. Set `SHEET_METHOD=api` and enter your Spreadsheet Name in `.env`.

---

## Step 2: Telegram API Credentials

To listen to Telegram messages, you need to register an API Application.

1. Go to [my.telegram.org](https://my.telegram.org/) and log in with your phone number.
2. Go to **API development tools**.
3. Create a new application (fill in a dummy title and short name).
4. Save the **App api_id** (an integer) and **App api_hash** (a string).
5. Paste these values into the `.env` file.

---

## Step 3: Configuration (`.env`)

Open the `.env` file in this directory and fill out the values:

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Telegram Channel/Group Identifier
# You can use the channel link (e.g. https://t.me/job_channel) or username (e.g. @job_channel).
# Tip: You can comma-separate multiple groups/channels (e.g. @jobs_a, @jobs_b)
TELEGRAM_GROUP_IDENTIFIER=https://t.me/your_target_channel

# Sheets Configuration (set webhook and paste your Apps Script Web App URL)
SHEET_METHOD=webhook
GOOGLE_SHEET_WEBHOOK_URL=https://script.google.com/macros/s/XXXXX/exec
```

---

## Step 4: Running the App

### 1. Activating Virtual Environment
Before running, you can activate the local Python environment:
```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

### 2. Run the Script
Execute the script:
```bash
python main.py
```
*(Alternatively, run directly without activation: `.\venv\Scripts\python.exe main.py`)*

### 3. Verification & First Run Login
On the very first run, if you did not provide a `TELEGRAM_BOT_TOKEN`, the console will ask:
- **Phone number**: Enter your phone number in full international format (e.g., `+1234567890` or `+919876543210`).
- **OTP Code**: Enter the login code Telegram sent to your active devices.
- **2FA Password**: (Only if you have Two-Step Verification enabled).

Once authenticated, it will create a `job_sheet_session.session` file to keep you logged in. You won't have to authenticate again.

The bot will now log `Successfully logged in` and listen continuously. Whenever a new job matching the pattern is posted, it will print it to the terminal and automatically append it to your Google Sheet!
