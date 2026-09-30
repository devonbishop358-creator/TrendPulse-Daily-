import streamlit as st
from pathlib import Path
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import pickle

st.set_page_config(page_title="TrendPulse Daily", page_icon="📈", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
DB = BASE_DIR / "trendpulse_data.json"
VIDEO_DIR = BASE_DIR / "trendpulse_videos"
AUDIO_DIR = BASE_DIR / "trendpulse_audio"
CREDS_DIR = BASE_DIR / "creds"

VIDEO_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)
CREDS_DIR.mkdir(exist_ok=True)

def load():
    if not DB.exists():
        return {"drafts": [], "topics": []}
    try:
        data = json.loads(DB.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            data = {}
        data.setdefault("drafts", [])
        data.setdefault("topics", [])
        
        for draft in data["drafts"]:
            draft.setdefault("id", 0)
            draft.setdefault("topic", draft.get("title", "Untitled"))
            draft.setdefault("title", draft.get("topic", "Untitled"))
            draft.setdefault("script", "")
            draft.setdefault("status", "Awaiting approval")
            draft.setdefault("created", "")
            draft.setdefault("audio", "")
            draft.setdefault("video", "")
            draft.setdefault("youtube_url", "")
            draft.setdefault("youtube_video_id", "")
        
        return data
    except Exception:
        return {"drafts": [], "topics": []}

def save(data):
    try:
        DB.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        st.error(f"Error saving: {e}")

data = load()

def get_trends():
    url = "https://trends.google.com/trending/rss?geo=ZA"
    try:
        response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(response.content)
        topics = []
        for item in root.findall(".//item"):
            title = item.findtext("title")
            if title:
                topics.append(title.strip())
        return topics[:20]
    except Exception:
        st.error("Could not load Google Trends.")
        return []

def make_script(topic):
    return f"""Welcome to TrendPulse Daily.

Today's trending topic is {topic}.

This topic is currently receiving search interest from people in South Africa.

In this video, we look at what people are searching for and why this topic is receiving attention.

Search trends can change quickly.

Trending searches show what people are looking for, but they do not automatically confirm that every claim or report surrounding a topic is true.

For important developments, viewers should always check reliable and confirmed information.

We will continue monitoring this topic and provide updates when reliable information becomes available.

That is today's TrendPulse Daily update.

Subscribe to TrendPulse Daily for more daily trending topics from South Africa."""

def create_draft(topic):
    ids = []
    for draft in data["drafts"]:
        try:
            draft_id = draft.get("id", 0)
            if draft_id:
                ids.append(int(draft_id))
        except:
            pass
    
    new_id = max(ids) + 1 if ids else 1
    
    draft = {
        "id": new_id,
        "topic": topic,
        "title": topic,
        "script": make_script(topic),
        "status": "Awaiting approval",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "audio": "",
        "video": "",
        "youtube_url": "",
        "youtube_video_id": ""
    }
    data["drafts"].append(draft)
    save(data)

def authenticate_youtube():
    """Authenticate with YouTube API"""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
    except ImportError:
        st.error("Missing YouTube dependencies")
        st.info("Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return None
    
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    TOKEN_FILE = CREDS_DIR / 'youtube_token.pickle'
    CREDENTIALS_FILE = CREDS_DIR / 'youtube_credentials.json'

    creds = None

    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                st.error("YouTube credentials.json not found!")
                st.info("Get it from: https://console.cloud.google.com")
                return None

            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                st.error(f"Auth error: {e}")
                return None

        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return creds

def upload_to_youtube(video_path, title, description, tags):
    """Upload video to YouTube"""
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        creds = authenticate_youtube()
        if not creds:
            return None, "YouTube authentication failed"

        youtube = build('youtube', 'v3', credentials=creds)

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '25'
            },
            'status': {
                'privacyStatus': 'public'
            }
        }

        media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)

        insert_request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = insert_request.next_chunk()

        video_id = response['id']
        return video_id, f"https://www.youtube.com/watch?v={video_id}"

    except Exception as e:
        return None, f"Upload failed: {str(e)}"

st.title("📈 TrendPulse Daily")
st.caption("Daily trend discovery and approval workflow")

tab1, tab2, tab3, tab4 = st.tabs(["Approval Queue", "Trends", "Analytics", "Settings"])

with tab1:
    st.header("Approval Queue")
    st.info("Nothing publishes without your approval.")
    
    if not data["drafts"]:
        st.info("No drafts are waiting for approval.")
    else:
        for draft in reversed(data["drafts"]):
            st.divider()
            
            topic = draft.get("topic", "Untitled")
            status = draft.get("status",
