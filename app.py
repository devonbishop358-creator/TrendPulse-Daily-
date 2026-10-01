import streamlit as st
from pathlib import Path
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import pyttsx3

st.set_page_config(page_title="TrendPulse Daily", page_icon="📈", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
DB = BASE_DIR / "trendpulse_data.json"
VIDEO_DIR = BASE_DIR / "trendpulse_videos"
AUDIO_DIR = BASE_DIR / "trendpulse_audio"

VIDEO_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)

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
            draft.setdefault("topic", "Untitled")
            draft.setdefault("title", "Untitled")
            draft.setdefault("script", "")
            draft.setdefault("status", "Awaiting approval")
            draft.setdefault("created", "")
            draft.setdefault("audio", "")
            draft.setdefault("video", "")
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
    return f"Welcome to TrendPulse Daily. Today's trending topic is {topic}. This topic is currently receiving search interest from people in South Africa. In this video, we look at what people are searching for and why this topic is receiving attention. Search trends can change quickly. For important developments, viewers should always check reliable and confirmed information. That is today's TrendPulse Daily update. Subscribe for more daily trending topics from South Africa."

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
        "youtube_url": ""
    }
    data["drafts"].append(draft)
    save(data)

def create_voiceover(script, draft_id):
    try:
        audio_path = AUDIO_DIR / f"trendpulse_{draft_id}.wav"
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.9)
        engine.save_to_file(script, str(audio_path))
        engine.runAndWait()
        return str(audio_path) if audio_path.exists() else None
    except Exception as e:
        st.error(f"Voiceover failed: {str(e)}")
        return None

st.title("📈 TrendPulse Daily")
st.caption("Daily trend discovery and YouTube monetization")

tab1, tab2, tab3, tab4 = st.tabs(["Approval Queue", "Trends", "Analytics", "Settings"])

with tab1:
    st.header("Approval Queue")
    st.info("Nothing publishes without your approval.")
    if not data["drafts"]:
        st.info("No drafts yet.")
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
            st.text_area("Script", script, height=120, disabled=True, key=f"s_{draft['id']}")
            
            if status == "Awaiting approval":
                col1, col2 = st.columns(2)
                if col1.button("✅ APPROVE", key=f"a_{draft['id']}"):
                    draft["status"] = "Approved"
                    save(data)
                    st.success("Approved!")
                    st.rerun()
                if col2.button("❌ REJECT", key=f"r_{draft['id']}"):
                    draft["status"] = "Rejected"
                    save(data)
                    st.warning("Rejected!")
                    st.rerun()
            elif status == "Approved":
                st.success("✅ Approved!")
                if st.button("🎤 Create Voiceover", key=f"v_{draft['id']}"):
                    with st.spinner("Creating voiceover..."):
                        audio = create_voiceover(script, draft['id'])
                        if audio:
                            draft["audio"] = audio
                            save(data)
                            st.success("Voiceover created!")
                            st.audio(audio)
                        st.rerun()
                if draft.get("audio"):
                    st.audio(draft["audio"])
            elif status == "Rejected":
                st.error("❌ Rejected!")

with tab2:
    st.header("🇿🇦 Google Trends")
    if st.button("🔄 REFRESH TRENDS"):
        trends = get_trends()
        if trends:
            data["topics"] = trends
            save(data)
            st.success(f"Found {len(trends)} trends!")
        st.rerun()
    trends = data.get("topics", [])
    if trends:
        selected = st.selectbox("Choose topic", trends)
        if st.button("📝 CREATE DRAFT"):
            create_draft(selected)
            st.success("Draft created!")
            st.rerun()
        st.subheader("Trends")
        for i, t in enumerate(trends, 1):
            st.write(f"{i}. {t}")
    else:
        st.info("Click refresh to load trends.")

with tab3:
    st.header("📊 Analytics")
    drafts = data.get("drafts", [])
    total = len(drafts)
    approved = len([d for d in drafts if d.get("status") == "Approved"])
    rejected = len([d for d in drafts if d.get("status") == "Rejected"])
    pending = len([d for d in drafts if d.get("status") == "Awaiting approval"])
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", total)
    col2.metric("Approved", approved)
    col3.metric("
