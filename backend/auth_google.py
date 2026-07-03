from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDS_FILE = r"C:\Proyectos\Jarvis\backend\data\google_credentials.json"
TOKEN_FILE = r"C:\Proyectos\Jarvis\backend\data\google_token.json"

flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
creds = flow.run_local_server(port=8888)

with open(TOKEN_FILE, "w") as f:
    f.write(creds.to_json())

print("Google Calendar autorizado!")
print("Token guardado en: " + TOKEN_FILE)
