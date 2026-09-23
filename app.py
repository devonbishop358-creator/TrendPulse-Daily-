import streamlit as st
from pathlib import Path
import json
import pandas as pd
import requests
import xml.etree.ElementTree as ET
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

GOOGLE_TRENDS_RSS = "https://trends.google.com/trending/rss?geo=ZA"


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
        raw = json.loads(
            DATA_FILE.read_text(encoding="utf-8")
        )

        if isinstance(raw, dict):
            return {
                "drafts": raw.get("drafts", []),
                "topics": raw.get("topics", []),
                "metrics": raw.get("metrics", [])
            }

        if isinstance(raw, list):
            return {
                "drafts": raw,
                "topics": [],
                "metrics": []
            }

    except Exception:
        pass

    return {
        "drafts": [],
        "topics": [],
        "metrics": []
    }


def save_database(database):
    """Save TrendPulse database."""

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
# GOOGLE TRENDS
# ============================================================

def fetch_google_trends():
    """
    Fetch current Google Trends RSS results for South Africa.
    """

    try:
        response = requests.get(
            GOOGLE_TRENDS_RSS,
            timeout=20,
            headers={
                "User-Agent": "TrendPulse Daily/1.0"
            }
        )

        response.raise_for_status()

        root = ET.fromstring(response.content)

        items = []

        for item in root.findall(".//item"):

            title_element = item.find("title")
            pubdate_element = item.find("pubDate")
            traffic_element = item.find(
                "{https://trends.google.com/trending/rss}approx_traffic"
            )

            title = (
                title_element.text.strip()
                if title_element is not None
                and title_element.text
                else ""
            )

            pubdate = (
                pubdate_element.text.strip()
                if pubdate_element is not None
                and pubdate_element.text
                else ""
            )

            traffic = (
                traffic_element.text.strip()
                if traffic_element is not None
                and traffic_element.text
                else ""
            )

            if title:
                items.append(
                    {
                        "title": title,
                        "traffic": traffic,
                        "published": pubdate,
                        "source": "Google Trends"
                    }
                )

        return items

    except Exception as error:

        st.error(
            f"Could not load Google Trends: {error}"
        )

        return []


# ============================================================
# ADD REAL TRENDS TO DATABASE
# ============================================================

def import_google_trends(database):
    """Import new Google Trends topics without duplicates."""

    live_trends = fetch_google_trends()

    if not live_trends:
        return 0

    existing_titles = {
        get_title(item).strip().lower()
        for item in database["drafts"]
        if isinstance(item, dict)
    }

    added = 0

    for trend in live_trends[:10]:

        title = trend["title"]

        if title.strip().lower() in existing_titles:
            continue

        draft = {
            "id": len(database["drafts"]) + 1,
            "title": title,
            "niche": "Trending topics",
            "status": "Draft",
            "scheduled_for": "",
            "copyright_check": "Pending",
            "source": "Google Trends",
            "traffic": trend.get("traffic", ""),
            "published": trend.get("published", ""),
            "script": ""
        }

        database["drafts"].append(draft)

        existing_titles.add(
            title.strip().lower()
        )

        added += 1

    save_database(database)

    return added


# ============================================================
# FREE SCRIPT GENERATOR
# ============================================================

def create_script(item):

    title = get_title(item)

    return f"""
Today we are looking at {title}.

This topic is currently appearing among trending searches
on Google Trends in South Africa.

In this video, we will explain what {title} is, why people
are searching for it, and the important information viewers
should know.

We will look at the key details surrounding the topic and
provide useful context so that the story is easier to understand.

Because trending stories can develop quickly, viewers should
check the latest information before relying on details that
may change.

That is today's TrendPulse Daily update on {title}.

Follow TrendPulse Daily for more daily trend updates.
""".strip()


# ============================================================
# FREE CAPCUT PRODUCTION PACK
# ============================================================

def create_production_pack(item):

    title = get_title(item)

    description = (
        f"TrendPulse Daily explains what is happening with "
        f"{title}, why people are searching for it, and what "
        f"viewers should know."
    )

    script = item.get("script", "")

    if not script:
        script = create_script(item)

    pack = f"""
============================================================
TRENDPULSE DAILY — FREE CAPCUT PRODUCTION PACK
============================================================

VIDEO TOPIC
{title}

SOURCE
Google Trends — South Africa

FORMAT
16:9 YouTube video
Target length: 3–6 minutes

============================================================
NARRATION SCRIPT
============================================================

{script}

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
Explain what is happening and why people are searching for it.


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
Explain why viewers may be interested in the story.


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
Google Trends — South Africa

HASHTAGS

#TrendPulseDaily
#GoogleTrends
#Trending
#TrendingNow
#SouthAfrica

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
[ ] Verify the latest information
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
# LIVE GOOGLE TRENDS BUTTON
# ============================================================

st.subheader("🇿🇦 South Africa Google Trends")

st.write(
    "Import the latest trending searches from Google Trends."
)

if st.button(
    "🔄 GET LATEST GOOGLE TRENDS",
    width="stretch"
):

    added = import_google_trends(database)

    if added > 0:

        st.success(
            f"{added} new trending topic(s) imported."
        )

        st.rerun()

    else:

        st.info(
            "No new trends were added. "
            "Existing trends may already be in the database."
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

        st.info(
            "No trend drafts available. "
            "Click GET LATEST GOOGLE TRENDS above."
        )

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
                        item["approved_at"] = (
                            datetime.now().isoformat()
                        )

                        save_database(database)

                        st.success(
                            "Trend approved."
                        )

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

                        st.warning(
                            "Trend rejected."
                        )

                        st.rerun()

                # ------------------------------------------------
                # CAPCUT PACK
                # ------------------------------------------------

                with col3:

                    if st.button(
                        "PREPARE CAPCUT PACK",
                        key=f"pack_{index}",
                        width="stretch"
                    ):

                        if not item.get("script"):

                            item["script"] = create_script(item)

                            save_database(database)

                        pack = create_production_pack(item)

                        st.session_state[
                            f"production_pack_{index}"
                        ] = pack

                        st.success(
                            "Free CapCut production pack prepared."
                        )

                # ------------------------------------------------
                # DOWNLOAD PACK
                # ------------------------------------------------

                pack_key = f"production_pack_{index}"

                if pack_key in st.session_state:

                    st.download_button(
                        "⬇️ DOWNLOAD VIDEO PRODUCTION PACK",
                        data=st.session_state[pack_key],
                        file_name=(
                            "trendpulse_"
                            + title[:40]
                            .replace(" ", "_")
                            .replace("/", "_")
                            + "_production_pack.txt"
                        ),
                        mime="text/plain",
                        key=f"download_pack_{index}",
                        width="stretch"
                    )

                    st.text_area(
                        "Production pack preview",
                        st.session_state[pack_key],
                        height=500,
                        key=f"preview_pack_{index}"
                    )


# ============================================================
# TRENDS
# ============================================================

with trends_tab:

    st.header("Live Trends")

    if not drafts:

        st.info(
            "No trends available yet."
        )

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
                    ),
                    "Traffic": item.get(
                        "traffic",
                        ""
                    ),
                    "Published": item.get(
                        "published",
                        ""
                    )
                }
            )

        if rows:

            st.dataframe(
                pd.DataFrame(rows),
                width="stretch"
            )

        else:

            st.info(
                "No valid trend records found."
            )


# ============================================================
# ANALYTICS
# ============================================================

with analytics_tab:

    st.header("Analytics")

    valid_drafts = [
        item for item in drafts
        if isinstance(item, dict)
    ]

    total = len(valid_drafts)

    approved = len(
        [
            item for item in valid_drafts
            if item.get("status") == "Approved"
        ]
    )

    rejected = len(
        [
            item for item in valid_drafts
            if item.get("status") == "Rejected"
        ]
    )

    draft_count = len(
        [
            item for item in valid_drafts
            if item.get("status") == "Draft"
        ]
    )

    awaiting_youtube = len(
        [
            item for item in valid_drafts
            if "awaiting YouTube" in item.get(
                "status",
                ""
            )
        ]
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total trends",
        total
    )

    col2.metric(
        "New drafts",
        draft_count
    )

    col3.metric(
        "Approved",
        approved
    )

    col4.metric(
        "Awaiting YouTube",
        awaiting_youtube
    )

    st.write(
        f"Rejected trends: {rejected}"
    )


# ============================================================
# SETTINGS
# ============================================================

with settings_tab:

    st.header("Settings")

    st.subheader("Trend source")

    st.write(
        "Google Trends — South Africa"
    )

    st.write(
        "The app reads the Google Trends RSS feed for South Africa."
    )

    st.subheader("Video workflow")

    st.write(
        "Google Trends → TrendPulse → Approval → "
        "Free CapCut Production Pack → CapCut → YouTube"
    )

    st.success(
        "This workflow does not use paid OpenAI video generation."
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

    st.caption(
        "Google Trends data should be attributed to Google when reused."
    )
