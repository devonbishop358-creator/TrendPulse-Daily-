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
        data.setdefault("drafts", [])
        data.setdefault("topics", [])
        return data
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
    return f"Welcome to TrendPulse Daily. Today trending: {topic}. Subscribe!"

def create_draft(topic):
    ids = [int(d.get("id", 0)) for d in data["drafts"] if d.get("id")]
    new_id = max(ids) + 1 if ids else 1
    draft = {"id": new_id, "topic": topic, "script": make_script(topic), "status": "Awaiting approval", "created": datetime.now().strftime("%Y-%m-%d"), "audio": ""}
    data["drafts"].append(draft)
    save(data)

st.title("📈 TrendPulse Daily")

tab1, tab2, tab3, tab4 = st.tabs(["Queue", "Trends", "Analytics", "Settings"])

with tab1:
    st.header("Approval Queue")
    if not data["drafts"]:
        st.info("No drafts")
    else:
        for draft in reversed(data["drafts"]):
            st.divider()
            st.subheader(draft.get("topic"))
            st.write(f"Status: {draft.get('status')}")
            st.text_area("Script", draft.get("script"), disabled=True, key=f"s_{draft['id']}")
            if draft.get("status") == "Awaiting approval":
                col1, col2 = st.columns(2)
                if col1.button("APPROVE", key=f"a_{draft['id']}"):
                    draft["status"] = "Approved"
                    save(data)
                    st.rerun()
                if col2.button("REJECT", key=f"r_{draft['id']}"):
                    draft["status"] = "Rejected"
                    save(data)
                    st.rerun()
            elif draft.get("status") == "Approved":
                st.success("Approved")

with tab2:
    st.header("Google Trends")
    if st.button("Refresh"):
        trends = get_trends()
        if trends:
            data["topics"] = trends
            save(data)
        st.rerun()
    if data.get("topics"):
        sel = st.selectbox("Topic", data["topics"])
        if st.button("Create Draft"):
            create_draft(sel)
            st.rerun()

with tab3:
    st.header("Analytics")
    drafts = data.get("drafts", [])
    col1, col2, col3 = st.columns(3)
    col1.metric("Total", len(drafts))
    col2.metric("Approved", len([d for d in drafts if d.get("status") == "Approved"]))
    col3.metric("Pending", len([d for d in drafts if d.get("status") == "Awaiting approval"]))

with tab4:
    st.header("Settings")
    st.write("TrendPulse Daily is ready!")
