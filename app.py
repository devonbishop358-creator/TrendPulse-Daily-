import streamlit as st
from pathlib import Path
import json
import re
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="TrendPulse Daily",
    page_icon="📈",
    layout="wide"
)

DATA_FILE = Path("trendpulse_data.json")


def load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_data(data):
    DATA_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def get_title(item):
    return (
        item.get("title")
        or item.get("topic")
        or item.get("name")
        or "Untitled trend"
    )


def create_production_pack(item):
    title = get_title(item)
    description = item.get("description", "")
    source = item.get("source", "Google Trends")

    script = f"""TRENDPULSE DAILY VIDEO SCRIPT

Topic: {title}

INTRODUCTION
Today we are looking at a topic that is attracting attention right now:
{title}

MAIN STORY
This topic has been identified through current trend monitoring.
Explain what the topic is, why people are discussing it, and what viewers
should know.

KEY POINTS
1. Explain the basic background.
2. Describe the latest development or reason for interest.
3. Explain why this matters to the audience.
4. Mention any important uncertainty or unanswered questions.

CONCLUSION
That is the latest overview of {title}.
Follow TrendPulse Daily for more concise updates on topics people are watching.

Source: {source}
"""

    scene_plan = f"""TRENDPULSE DAILY CAPCUT SCENE PLAN

VIDEO TITLE:
{title}

FORMAT:
16:9 YouTube video
Target length: 3–6 minutes

SCENE 1 — OPENING
Visual: Bold title card showing the topic.
On-screen text: {title}

SCENE 2 — WHAT IS HAPPENING?
Visual: Relevant stock footage, news-style background, or screenshots.
Narration: Introduce the topic and explain why it is trending.

SCENE 3 — IMPORTANT DETAILS
Visual: Two or three relevant images or short video clips.
Narration: Explain the key facts and background.

SCENE 4 — WHY PEOPLE CARE
Visual: People, locations, products, or situations connected to the topic.
Narration: Explain the impact or significance.

SCENE 5 — SUMMARY
Visual: Clean summary card with the main takeaway.
Narration: Summarise the story.

SCENE 6 — OUTRO
Visual: TrendPulse Daily branding.
On-screen text: Follow for daily trend updates.
"""

    metadata = f"""YOUTUBE METADATA

TITLE:
{title}

DESCRIPTION:
{description}

Suggested description:
TrendPulse Daily explains what is trending, why it matters, and what you
should know. Subscribe for concise daily updates on important topics.

HASHTAGS:
#TrendPulseDaily #Trending #News #Explained #DailyUpdate
"""

    return (
        script
        + "\n\n" + "=" * 60 + "\n\n"
        + scene_plan
        + "\n\n" + "=" * 60 + "\n\n"
        + metadata
    )


st.title("📈 TrendPulse Daily")
st.caption("Trend discovery and free video production workflow")

data = load_data()

tabs = st.tabs([
    "Approval Queue",
    "Trends",
    "Analytics",
    "Settings"
])

with tabs[0]:
    st.header("Approval Queue")

    if not data:
        st.info("No trend drafts available yet.")
    else:
        for index, item in enumerate(data):
            title = get_title(item)
            status = item.get("status", "Draft")

            with st.expander(f"{title} — {status}"):
                st.write(item)

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button(
                        "APPROVE",
                        key=f"approve_{index}"
                    ):
                        item["status"] = "Approved"
                        item["approved_at"] = datetime.now().isoformat()
                        save_data(data)
                        st.success("Trend approved.")
                        st.rerun()

                with col2:
                    if st.button(
                        "REJECT",
                        key=f"reject_{index}"
                    ):
                        item["status"] = "Rejected"
                        save_data(data)
                        st.warning("Trend rejected.")
                        st.rerun()

                with col3:
                    if st.button(
                        "PREPARE CAPCUT PACK",
                        key=f"pack_{index}"
                    ):
                        pack = create_production_pack(item)
                        st.session_state[f"pack_{index}"] = pack
                        st.success("Free production pack prepared.")

                if f"pack_{index}" in st.session_state:
                    st.download_button(
                        "DOWNLOAD VIDEO PRODUCTION PACK",
                        data=st.session_state[f"pack_{index}"],
                        file_name="trendpulse_video_pack.txt",
                        mime="text/plain",
                        key=f"download_{index}"
                    )

                    st.text_area(
                        "Production pack preview",
                        st.session_state[f"pack_{index}"],
                        height=350,
                        key=f"preview_{index}"
                    )

with tabs[1]:
    st.header("Trends")

    if data:
        rows = []
        for item in data:
            rows.append({
                "Topic": get_title(item),
                "Status": item.get("status", "Draft"),
                "Source": item.get("source", "Unknown")
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True
        )
    else:
        st.info("No trends collected yet.")

with tabs[2]:
    st.header("Analytics")

    total = len(data)
    approved = sum(
        1 for item in data
        if item.get("status") == "Approved"
    )
    rejected = sum(
        1 for item in data
        if item.get("status") == "Rejected"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Total trends", total)
    col2.metric("Approved", approved)
    col3.metric("Rejected", rejected)

with tabs[3]:
    st.header("Settings")

    st.info(
        "This version uses a free workflow. It prepares scripts, scene plans "
        "and YouTube metadata for manual production in CapCut."
    )

    st.write("No paid OpenAI video-generation API is used.")
