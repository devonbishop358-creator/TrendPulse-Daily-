import streamlit as st
from pathlib import Path
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

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
        return json.loads(DB.read_text(encoding="utf-8-sig"))
    except:
        return {"drafts": [], "topics": []}

def save(data):
    DB.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

data = load()

def get_trends():
    url = "https://trends.google.com/trending/rss?geo=ZA"
    try:
        response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(response.content)
        topics = [item.findtext("title") for item in root.findall(".//item") if item.findtext("title")]
        return topics[:20]
    except:
        return []

def make_script(topic):
    return f"Welcome to TrendPulse Daily. Today's trending topic is {topic}. This is currently trending in South Africa. Subscribe for daily updates!"

def create_draft(topic):
    ids = [int(d.get("id", 0)) for d in data["drafts"] if d.get("id")]
    draft_id = max(ids) + 1 if ids else 1
    draft = {
        "id": draft_id,
        "topic": topic,
        "title": topic,
        "script": make_script(topic),
        "status": "Awaiting approval",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "audio": "",
        "video": ""
    }
    data["drafts"].append(draft)
    save(data)

st.title("📈 TrendPulse Daily")
st.caption("Daily trend discovery and approval workflow")

tab1, tab2, tab3, tab4 = st.tabs(["Approval Queue", "Trends", "Analytics", "Settings"])

with tab1:
    st.header("Approval Queue")
    if not data["drafts"]:
        st.info("No drafts waiting for approval.")
    else:
        for draft in reversed(data["drafts"]):
            st.divider()
            st.subheader(draft["topic"])
            st.write("Status:", draft["status"])
            st.write("Created:", draft["created"])
            
            col1, col2 = st.columns(2)
            if col1.button("APPROVE", key=f"approve_{draft['id']}"):
                draft["status"] = "Approved"
                save(data)
                st.success("Approved!")
                st.rerun()
            if col2.button("REJECT", key=f"reject_{draft['id']}"):
                draft["status"] = "Rejected"
                save(data)
                st.warning("Rejected!")
                st.rerun()

with tab2:
    st.header("🇿🇦 South Africa Google Trends")
    if st.button("REFRESH GOOGLE TRENDS"):
        trends = get_trends()
        data["topics"] = trends
        save(data)
        st.success(f"Found {len(trends)} trends!")
        st.rerun()
    
    trends = data.get("topics", [])
    if trends:
        selected = st.selectbox("Choose a topic", trends)
        if st.button("CREATE DRAFT"):
            create_draft(selected)
            st.success("Draft created!")
            st.rerun()
        
        st.subheader("Current Trends")
        for i, topic in enumerate(trends, 1):
            st.write(f"{i}. {topic}")
    else:
        st.info("Click REFRESH to load trends.")

with tab3:
    st.header("📊 Analytics")
    drafts = data.get("drafts", [])
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Drafts", len(drafts))
    col2.metric("Approved", len([d for d in drafts if d.get("status") == "Approved"]))
    col3.metric("Rejected", len([d for d in drafts if d.get("status") == "Rejected"]))
    col4.metric("Pending", len([d for d in drafts if d.get("status") == "Awaiting approval"]))

with tab4:
    st.header("Settings")
    st.write("**Workflow:**")
    st.code("Google Trends → TrendPulse → Approval → YouTube")
    st.write("**Format:** 16:9 YouTube videos")
    st.write("**Region:** South Africa (ZA)")
    st.success("✅ App is ready!")
