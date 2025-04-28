import os
from dotenv import load_dotenv
from google.cloud import firestore
from google.oauth2 import service_account


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL") 

def get_firestore_client() -> firestore.Client:
    """
    Get Firestore client using credentials from environment variables.
    """
    credentials_info = {
        "type": "service_account",
        "project_id": os.getenv("GOOGLE_APPLICATION_CREDENTIALS_PROJECT_ID"),
        "private_key_id": "not-required",
        "private_key": os.getenv("GOOGLE_APPLICATION_CREDENTIALS_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("GOOGLE_APPLICATION_CREDENTIALS_CLIENT_EMAIL"),
        "client_id": "not-required",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('GOOGLE_APPLICATION_CREDENTIALS_CLIENT_EMAIL').replace('@', '%40')}"
    }

    for key, value in credentials_info.items():
        if value is None:
            raise Exception(f"{key} is missing in environment variables.")

    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    db = firestore.Client(credentials=credentials)
    return db
