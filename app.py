import streamlit as st
from pathlib import Path
import json
import pandas as pd
from datetime import datetime

# ============================================================
# APP CONFIG
# ============================================================

st.set_page_config(
    page_title="TrendPulse Daily",
    page_icon="📈",
    layout="wide"
)

DATA_FILE = Path("trendpulse_data.json")


# ============================================================
# DATA FUNCTIONS
# ============================================================

def load_database():
    """Load the complete TrendPulse database."""
    if not DATA_FILE.exists():
        return {
            "drafts": [],
            "topics": [],
            "metrics": []
        }

    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))

        if isinstance(raw, dict):
            return {
                "drafts": raw.get("drafts", []),
                "topics": raw.get("topics", []),
                "metrics": raw.get("metrics", [])
            }

        # Compatibility with older list-only versions
        if isinstance(raw, list):
            return {
                "drafts": raw,
                "topics": [],
                "metrics": []
            }

        return {
            "drafts": [],
            "topics": [],
            "metrics": []
        }

    except Exception:
        return {
            "drafts": [],
            "topics": [],
            "metrics": []
        }


def save_database(database):
    """Save the complete TrendPulse database."""
    DATA_FILE.write_text(
        json.dumps(
            database,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


def get_title(item):
    """Safely obtain a draft title."""
    if not isinstance(item, dict):
        return "Untitled trend"

    return (
        item.get("title")
        or item.get("topic")
        or item.get("name")
        or "Untitled trend"
    )


def get_status(item):
    """Safely obtain draft status."""
    if not isinstance(item, dict):
        return "Draft"

    return item.get("status", "Draft")


# ============================================================
# FREE CAPCUT PRODUCTION PACK
# ============================================================

def create_production_pack(item):
    """Create a free text production pack for CapCut."""

    title = get_title(item)

    if not isinstance(item, dict):
        item = {}

    description = item.get("description", "")
    source = item.get("source", "TrendPulse Daily")
    original_script = item.get("script", "")

    if not description:
        description = (
            f"TrendPulse Daily explains what is happening with "
            f"{title}, why people are paying attention, and what "
            f"viewers should know."
        )

    if not original_script or "Placeholder draft" in original_script:
        original_script = f"""
Today we are looking at {title}.

This topic has attracted attention through TrendPulse Daily's
trend monitoring.

In this video, we explain what the topic is, what has happened,
why people are discussing it, and what viewers should know.

We will also look at the important background and the key points
that help put the story into context.

As with any developing story, viewers should check the latest
information because details can change.

That is the TrendPulse Daily update on {title}.

Follow TrendPulse Daily for more daily trend updates.
""".strip()

    pack = f"""
============================================================
TRENDPULSE DAILY — FREE CAPCUT PRODUCTION PACK
============================================================

VIDEO TOPIC
{title}

FORMAT
16:9 YouTube video
Target length: 3–6 minutes

============================================================
NARRATION SCRIPT
============================================================

{original_script}

============================================================
CAPCUT SCENE PLAN
============================================================

SCENE 1 — OPENING
Duration: 10–20 seconds

Visual:
Use a strong relevant image or short video clip.

On-screen text:
{title}

Narration:
Introduce the topic and tell viewers what the video will explain.


SCENE 2 — WHAT IS HAPPENING?
Duration: 30–60 seconds

Visual:
Use relevant stock footage, photographs, screenshots or graphics.

Narration:
Explain what is happening and why the topic is attracting attention.


SCENE 3 — KEY DETAILS
Duration: 60–120 seconds

Visual:
Use 2–4 relevant images or video clips.

Narration:
Explain the main facts and important background.


SCENE 4 — WHY IT MATTERS
Duration: 45–90 seconds

Visual:
Show people, locations, products, events or other visuals
connected with the topic.

Narration:
Explain why viewers should care about the story.


SCENE 5 — SUMMARY
Duration: 20–40 seconds

Visual:
Use a clean summary card.

On-screen text:
KEY TAKEAWAYS

Narration:
Summarise the most important points.


SCENE 6 — OUTRO
Duration: 10–15 seconds

Visual:
TrendPulse Daily branding.

On-screen text:
FOLLOW FOR DAILY TREND UPDATES

Narration:
Thank viewers and invite them to follow TrendPulse Daily.

============================================================
YOUTUBE METADATA
============================================================

TITLE
{title}

DESCRIPTION

{description}

TrendPulse Daily provides concise explanations of topics
people are currently watching.

Subscribe for daily trend updates and easy-to-understand
explanations.

SOURCE
{source}

HASHTAGS

#TrendPulseDaily
#Trending
#News
#Explained
#DailyUpdate

============================================================
CAPCUT CHECKLIST
============================================================

[ ] Create a new 16:9 project
[ ] Add opening visual
[ ] Add narration
[ ] Add scene visuals
[ ] Add captions
[ ] Add background music if appropriate
[ ] Add TrendPulse Daily branding
[ ] Check spelling and facts
[ ] Watch the complete video
[ ] Export at 1080p
[ ] Upload to YouTube

============================================================
END OF PRODUCTION PACK
============================================================
"""

    return pack.strip()


# ============================================================
# LOAD DATABASE
# ============================================================

database = load_database()

drafts = database["drafts"]
topics = database["topics"]
metrics = database["metrics"]


# ============================================================
# HEADER
# ============================================================

st.title("📈 TrendPulse Daily")
st.caption(
    "Daily trend discovery, approval and free video production workflow"
)


# ============================================================
# TABS
# ============================================================

approval_tab, trends_tab, analytics_tab, settings_tab = st.tabs(
    [
        "Approval Queue",
        "Trends",
        "Analytics",
        "Settings"
    ]
)


# ============================================================
# APPROVAL QUEUE
# ============================================================

with approval_tab:

    st.header("Approval Queue")

    if not drafts:
        st.info("No trend drafts available.")

    else:

        for index, item in enumerate(drafts):

            if not isinstance(item, dict):
                continue

            title = get_title(item)
            status = get_status(item)

            with st.expander(
                f"{title} — {status}"
            ):

                st.write(item)

                col1, col2, col3 = st.columns(3)

                # ------------------------------------------------
                # APPROVE
                # ------------------------------------------------

                with col1:

                    if st.button(
                        "APPROVE",
                        key=f"approve_{index}",
                        width="stretch"
                    ):

                        item["status"] = "Approved"
                        item["approved_at"] = datetime.now().isoformat()

                        save_database(database)

                        st.success("Trend approved.")
                        st.rerun()

                # ------------------------------------------------
                # REJECT
                # ------------------------------------------------

                with col2:

                    if st.button(
                        "REJECT",
                        key=f"reject_{index}",
                        width="stretch"
                    ):

                        item["status"] = "Rejected"

                        save_database(database)

                        st.warning("Trend rejected.")
                        st.rerun()

                # ------------------------------------------------
                # PRODUCTION PACK
                # ------------------------------------------------

                with col3:

                    if st.button(
                        "PREPARE CAPCUT PACK",
                        key=f"pack_{index}",
                        width="stretch"
                    ):

                        pack = create_production_pack(item)

                        st.session_state[
                            f"production_pack_{index}"
                        ] = pack

                        st.success(
                            "Free CapCut production pack prepared."
                        )

                # ------------------------------------------------
                # SHOW DOWNLOAD
                # ------------------------------------------------

                pack_key = f"production_pack_{index}"

                if pack_key in st.session_state:

                    st.download_button(
                        "DOWNLOAD VIDEO PRODUCTION PACK",
                        data=st.session_state[pack_key],
                        file_name="trendpulse_video_pack.txt",
                        mime="text/plain",
                        key=f"download_pack_{index}",
                        width="stretch"
                    )

                    st.text_area(
                        "Production pack preview",
                        st.session_state[pack_key],
                        height=400,
                        key=f"preview_pack_{index}"
                    )


# ============================================================
# TRENDS
# ============================================================

with trends_tab:

    st.header("Trends")

    if not drafts:

        st.info("No trends available yet.")

    else:

        rows = []

        for item in drafts:

            if not isinstance(item, dict):
                continue

            rows.append(
                {
                    "Topic": get_title(item),
                    "Status": get_status(item),
                    "Source": item.get(
                        "source",
                        "Google Trends"
                    )
                }
            )

        if rows:

            st.dataframe(
                pd.DataFrame(rows),
                width="stretch"
            )

        else:

            st.info("No valid trend records found.")


# ============================================================
# ANALYTICS
# ============================================================

with analytics_tab:

    st.header("Analytics")

    total = len(
        [
            item for item in drafts
            if isinstance(item, dict)
        ]
    )

    approved = len(
        [
            item for item in drafts
            if isinstance(item, dict)
            and item.get("status") == "Approved"
        ]
    )

    rejected = len(
        [
            item for item in drafts
            if isinstance(item, dict)
            and item.get("status") == "Rejected"
        ]
    )

    awaiting_youtube = len(
        [
            item for item in drafts
            if isinstance(item, dict)
            and "awaiting YouTube" in item.get(
                "status",
                ""
            )
        ]
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total drafts",
        total
    )

    col2.metric(
        "Approved",
        approved
    )

    col3.metric(
        "Rejected",
        rejected
    )

    col4.metric(
        "Awaiting YouTube",
        awaiting_youtube
    )


# ============================================================
# SETTINGS
# ============================================================

with settings_tab:

    st.header("Settings")

    st.subheader("Video workflow")

    st.write(
        "TrendPulse Daily currently uses a free production workflow."
    )

    st.write(
        "The app prepares the topic, narration, scene plan and "
        "YouTube metadata for production in CapCut."
    )

    st.success(
        "No paid OpenAI video-generation API is used by this version."
    )

    st.subheader("Video format")

    st.write("• YouTube")
    st.write("• 16:9")
    st.write("• 3–6 minutes")
    st.write("• CapCut production workflow")

    st.subheader("Database")

    st.write(
        f"Drafts stored: {len(drafts)}"
    )

    st.write(
        f"Topics stored: {len(topics)}"
    )

    st.write(
        f"Metrics stored: {len(metrics)}"
    )
