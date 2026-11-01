"""
Google Calendar integration (100% free tier -- Google Calendar API has a
generous free quota for personal use, no billing needed).

Setup:
  1. Go to https://console.cloud.google.com/ -> create a project
  2. Enable "Google Calendar API"
  3. Create OAuth 2.0 Client ID credentials, type "Desktop app"
  4. Download the JSON as backend/credentials.json (gitignored)
  5. First run will open a browser to authorize; a token.json is cached
     afterwards so you won't need to log in again.
"""
from datetime import datetime, date
from typing import List, Dict
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.config import GOOGLE_CREDENTIALS_FILE, GOOGLE_TOKEN_FILE

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def _get_credentials():
    creds = None
    if os.path.exists(GOOGLE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"{GOOGLE_CREDENTIALS_FILE} not found. See google_calendar.py docstring for setup."
                )
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(GOOGLE_TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())
    return creds


def fetch_upcoming_events(days_ahead: int = 31) -> List[Dict]:
    """Returns [{title, date, description}] for events in the next N days."""
    creds = _get_credentials()
    service = build("calendar", "v3", credentials=creds)

    now = datetime.utcnow().isoformat() + "Z"
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=100,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    items = events_result.get("items", [])

    events = []
    for item in items:
        start = item["start"].get("dateTime", item["start"].get("date"))
        event_date = datetime.fromisoformat(start.replace("Z", "+00:00")).date()
        events.append(
            {
                "external_id": item.get("id"),
                "title": item.get("summary", "Untitled event"),
                "date": event_date,
                "description": item.get("description", ""),
            }
        )
    return events
