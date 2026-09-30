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
    DB.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

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
    return f"""Welcome to TrendPulse Daily. Today's trending topic is {topic}. This topic is currently receiving search interest from people in South Africa. In this video, we look at what people are searching for and why this topic is receiving attention. Search trends can change quickly. For important developments, viewers should always check reliable and confirmed information. That is today's TrendPulse Daily update. Subscribe for more daily trending topics from South Africa."""

def create_draft(topic):
    ids = []
    for draft in data["drafts"]:
        try:
            if draft.get("id"):
                ids.append(int(draft.get("id")))
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
            status = draft.get("status", "Awaiting approval")
            created = draft.get("created", "N/A")
            script = draft.get("script", "")
            
            st.subheader(topic)
            st.write(f"**Status:** {status}")
            st.write(f"**Created:** {created}")
            st.markdown("### 📝 Script")
            st.text_area("Video script", script, height=150, key=f"script_{draft['id']}", disabled=True)
            
            if status == "Awaiting approval":
                col1, col2 = st.columns(2)
                if col1.button("✅ APPROVE", key=f"approve_{draft['id']}"):
                    draft["status"] = "Approved"
                    save(data)
                    st.success("Approved!")
                    st.rerun()
                if col2.button("❌ REJECT", key=f"reject_{draft['id']}"):
                    draft["status"] = "Rejected"
                    save(data)
                    st.warning("Rejected!")
                    st.rerun()
            elif status == "Approved":
                st.success("✅ Approved!")
                video_path = draft.get("video", "")
                if video_path and Path(video_path).exists():
                    st.video(video_path)
                    st.download_button("⬇️ Download Video", data=Path(video_path).read_bytes(), file_name=Path(video_path).name, mime="video/mp4", key=f"dl_{draft['id']}")
                
                st.divider()
                st.subheader("🎬 Upload to YouTube")
                yt_title = st.text_input("YouTube Title", value=topic, key=f"yt_title_{draft['id']}")
                yt_desc = st.text_area("YouTube Description", value=f"Trending in South Africa: {topic}", height=100, key=f"yt_desc_{draft['id']}")
                yt_tags = st.text_input("Tags (comma-separated)", value="trending,south africa,news", key=f"yt_tags_{draft['id']}")
                
                if st.button("🚀 UPLOAD TO YOUTUBE", key=f"upload_{draft['id']}"):
                    if not video_path or not Path(video_path).exists():
                        st.error("No video file found!")
                    else:
                        st.info("Uploading to YouTube...")
                        st.warning("Note: YouTube upload requires OAuth credentials. See Settings tab.")
            elif status == "Rejected":
                st.error("❌ Rejected!")

with tab2:
    st.header("🇿🇦 South Africa Google Trends")
    st.write("Import the latest trending searches from Google Trends into your Approval Queue.")
    
    if st.button("🔄 REFRESH GOOGLE TRENDS"):
        trends = get_trends()
        if trends:
            data["topics"] = trends
            save(data)
            st.success(f"Found {len(trends)} trends!")
        st.rerun()
    
    trends = data.get("topics", [])
    
    if trends:
        selected = st.selectbox("Choose a topic", trends)
        if st.button("📝 CREATE DRAFT"):
            create_draft(selected)
            st.success("Draft created!")
            st.rerun()
        st.subheader("Current Trends")
        for i, topic in enumerate(trends, 1):
