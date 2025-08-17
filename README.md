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

