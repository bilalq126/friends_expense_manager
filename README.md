# friends_expense_manager

## Streamlit Cloud Setup

Make sure the following packages are installed:
- streamlit
- pyrebase
- firebase-admin

You can install them using:
```
pip install streamlit pyrebase firebase-admin
```
Or add them to your `requirements.txt` file.

## Securely Managing Firebase Credentials

**Do NOT upload `serviceAccountKey.json` to GitHub or make it public.**

Instead, use Streamlit Cloud secrets management:

1. **Remove `serviceAccountKey.json` from your repository.**
2. In Streamlit Cloud, go to your app's settings and add your credentials in the `secrets` section like this:
    ```
    [firebase]
    type = "service_account"
    project_id = "your_project_id"
    private_key_id = "your_private_key_id"
    private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
    client_email = "your_client_email"
    client_id = "your_client_id"
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url = "your_client_x509_cert_url"
    universe_domain = "googleapis.com"
    ```
3. In your code, load the credentials from Streamlit secrets:
    ```python
    import streamlit as st
    from firebase_admin import credentials

    firebase_creds = st.secrets["firebase"]
    cred = credentials.Certificate(dict(firebase_creds))
    ```

This keeps your credentials secure and private.

## Google Sheets Setup

To persist data across app restarts, this app uses Google Sheets:

1. **Create a Google Cloud Service Account:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or use existing
   - Enable Google Sheets API and Google Drive API
   - Create a service account and download the JSON key

2. **Add credentials to Streamlit Cloud secrets:**
   ```
   [gcp_service_account]
   type = "service_account"
   project_id = "your_project_id"
   private_key_id = "your_private_key_id"
   private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
   client_email = "your_service_account_email"
   client_id = "your_client_id"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "your_client_x509_cert_url"
   
   sheet_name = "Friends Expense Tracker"
   ```

3. **The app will automatically create a Google Sheet** or use an existing one with the specified name.

This approach ensures data persistence even when Streamlit Cloud puts the app to sleep.

## Sheety API Setup (Alternative to Google Sheets)

Sheety is simpler to set up than Google Sheets API:

1. **Create a Google Sheet:**
   - Go to [Google Sheets](https://sheets.google.com)
   - Create a new sheet named "Friends Expense Tracker"
   - Add column headers: `date`, `amount`, `payers`, `contributions`, `present`, `description`

2. **Connect to Sheety:**
   - Go to [Sheety.co](https://sheety.co)
   - Sign up and connect your Google Sheet
   - Enable both GET and POST permissions
   - Copy your API endpoints

3. **Add to Streamlit Cloud secrets:**
   ```
   [sheety]
   get_url = "https://api.sheety.co/your-id/friendsExpenseTracker/expenses"
   post_url = "https://api.sheety.co/your-id/friendsExpenseTracker/expenses"
   sheet_url = "https://docs.google.com/spreadsheets/d/your-sheet-id"
   ```

**Benefits of Sheety:**
- No Google Cloud setup required
- Simple REST API
- Automatic authentication
- Free tier available
- Direct Google Sheets integration

This approach is much simpler than Google Sheets API and still ensures data persistence.

