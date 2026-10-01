import streamlit as st
from pathlib import Path
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

st.set_page_config(page_title="TrendPulse Daily", page_icon="📈", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
DB = BASE_DIR / "trendpulse_data.json"

def load():
    if not DB.exists():
        return {"drafts": [], "topics": []}
    return json.loads(DB.read_text(encoding="utf-8-sig"))

def save(data):
    DB.write_text(json.dumps(data, indent=2), encoding="utf-8")

data = load()

def get_trends():
    url = "https://trends.google.com/trending/rss?geo=ZA"
    try:
        response = requests.get(url, timeout=20)
        root = ET.fromstring(response.content)
        return [item.findtext("title") for item in root.findall(".//item") if item.findtext("title")]
    except:
        return []

def create_draft(topic):
    ids = [int(d.get("id", 0)) for d in data["drafts"]]
    new_id = max(ids) + 1 if ids else 1
    data["drafts"].append({"id": new_id, "topic": topic, "status": "Awaiting approval", "created": datetime.now().strftime("%Y-%m-%d")})
    save(data)

st.title("TrendPulse Daily")

tab1, tab2, tab3 = st.tabs(["Queue", "Trends", "Analytics"])

with tab1:
    st.header("Approval Queue")
    if data["drafts"]:
        for draft in reversed(data["drafts"]):
            st.write(f"**{draft['topic']}** - {draft['status']}")
            if draft['status'] == "Awaiting approval":
                col1, col2 = st.columns(2)
                if col1.button("Approve", key=f"a{draft['id']}"):
                    draft['status'] = "Approved"
                    save(data)
                    st.rerun()
                if col2.button("Reject", key=f"r{draft['id']}"):
                    draft['status'] = "Rejected"
                    save(data)
                    st.rerun()

with tab2:
    st.header("Google Trends")
    if st.button("Refresh"):
        trends = get_trends()
        data["topics"] = trends
        save(data)
        st.rerun()
    if data.get("topics"):
        sel = st.selectbox("Select", data["topics"])
        if st.button("Create"):
            create_draft(sel)
            st.rerun()

with tab3:
    st.header("Stats")
    drafts = data.get("drafts", [])
    col1, col2 = st.columns(2)
    col1.metric("Total", len(drafts))
    col2.metric("Approved", len([d for d in drafts if d["status"] == "Approved"]))
