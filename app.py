import streamlit as st
from pathlib import Path
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# ============================================================
# TRENDPULSE DAILY
# Free Google Trends -> Approval Queue -> CapCut Production Pack
# ============================================================

st.set_page_config(
    page_title="TrendPulse Daily",
    page_icon="📈",
    layout="wide"
)

DATA_FILE = Path("trendpulse_data.json")
GOOGLE_TRENDS_RSS = "https://trends.google.com/trending/rss?geo=ZA"


# ============================================================
# DATABASE
# ============================================================

def default_database():
    return {
        "drafts": [
            {
                "id": 1,
                "title": "Example TrendPulse Daily draft",
                "niche": "Example",
                "status": "Draft",
                "scheduled_for": "20:00 SAST",
                "copyright_check": "Pending",
                "source": "Example",
                "traffic": "",
                "published": False,
                "script": ""
            }
        ],
        "topics": [],
        "metrics": {
            "videos_published": 0,
            "approved": 0,
            "rejected": 0
        }
    }


def load_database():
    if not DATA_FILE.exists():
        return default_database()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)

        if not isinstance(raw, dict):
            return default_database()

        if "drafts" not in raw or not isinstance(raw["drafts"], list):
            raw["drafts"] = []

        if "topics" not in raw or not isinstance(raw["topics"], list):
            raw["topics"] = []

        if "metrics" not in raw or not isinstance(raw["metrics"], dict):
            raw["metrics"] = {}

        raw["metrics"].setdefault("videos_published", 0)
        raw["metrics"].setdefault("approved", 0)
        raw["metrics"].setdefault("rejected", 0)

        return raw

    except Exception:
        return default_database()


def save_database(database):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(database, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Could not save database: {e}")


database = load_database()


# ============================================================
# HELPERS
# ============================================================

def get_title(item):
    if isinstance(item, dict):
        return str(item.get("title", "Untitled"))
    return str(item)


def get_status(item):
    if isinstance(item, dict):
        return str(item.get("status", "Draft"))
    return "Draft"


def next_draft_id():
    ids = []

    for draft in database["drafts"]:
        if isinstance(draft, dict):
            try:
                ids.append(int(draft.get("id", 0)))
            except Exception:
                pass

    return max(ids, default=0) + 1


def clean_topic(text):
    return " ".join(str(text).strip().split())


# ============================================================
# GOOGLE TRENDS
# ============================================================

def fetch_google_trends():
    try:
        response = requests.get(
            GOOGLE_TRENDS_RSS,
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0 TrendPulse Daily"
            }
        )

        response.raise_for_status()

        root = ET.fromstring(response.content)

        trends = []

        for item in root.findall(".//item"):
            title_element = item.find("title")
            pub_element = item.find("pubDate")

            if title_element is None:
                continue

            title = clean_topic(title_element.text or "")

            if not title:
                continue

            pub_date = (
                clean_topic(pub_element.text)
                if pub_element is not None and pub_element.text
                else ""
            )

            traffic = ""

            for child in item:
                tag = child.tag.lower()

                if "approx_traffic" in tag:
                    traffic = clean_topic(child.text or "")
                    break

            trends.append({
                "title": title,
                "time": pub_date,
                "traffic": traffic
            })

        return trends

    except Exception as e:
        st.error(f"Google Trends could not be loaded: {e}")
        return []


def import_google_trends():
    trends = fetch_google_trends()

    if not trends:
        return 0

    existing_titles = set()

    for draft in database["drafts"]:
        if isinstance(draft, dict):
            existing_titles.add(
                clean_topic(draft.get("title", "")).lower()
            )

    imported = 0

    for trend in trends[:10]:

        title = clean_topic(trend["title"])

        if not title:
            continue

        if title.lower() in existing_titles:
            continue

        new_id = next_draft_id()

        draft = {
            "id": new_id,
            "title": title,
            "niche": "Trending",
            "status": "Draft",
            "scheduled_for": "",
            "copyright_check": "Pending",
            "source": "Google Trends South Africa",
            "traffic": trend.get("traffic", ""),
            "trend_time": trend.get("time", ""),
            "published": False,
            "script": ""
        }

        database["drafts"].append(draft)

        # Also keep a simple topic record
        database["topics"].append({
            "title": title,
            "source": "Google Trends South Africa",
            "time": trend.get("time", ""),
            "traffic": trend.get("traffic", "")
        })

        existing_titles.add(title.lower())

        imported += 1

    save_database(database)

    return imported


# ============================================================
# SCRIPT GENERATION
# ============================================================

def create_script(topic):
    return f"""TRENDPULSE DAILY VIDEO SCRIPT

Topic: {topic}

INTRODUCTION
Today we're looking at a topic that is currently trending in South Africa: {topic}.

WHAT IS TRENDING
{topic} is currently appearing among searches being made by South African users.

WHY PEOPLE ARE SEARCHING
The reason a topic begins trending can vary. It may be connected to breaking news,
sport, entertainment, a public event, a person, a product, or a developing story.

WHAT TO KNOW
Before publishing, check the latest reliable information about {topic}.
Use current sources and avoid presenting rumours or unverified claims as facts.

KEY TAKEAWAYS
• {topic} is currently trending.
• Search interest can change quickly.
• Check current sources before publishing.
• Separate confirmed information from speculation.

OUTRO
That's the latest TrendPulse Daily update.
Subscribe for more daily trending topics and news updates.
"""


# ============================================================
# CAPCUT PRODUCTION PACK
# ============================================================

def create_production_pack(draft):
    topic = get_title(draft)

    script = draft.get("script", "").strip()

    if not script:
        script = create_script(topic)

    pack = f"""==================================================
TRENDPULSE DAILY - CAPCUT VIDEO PRODUCTION PACK
==================================================

TOPIC
{topic}

FORMAT
16:9 YouTube video

TARGET LENGTH
3-6 minutes

SOURCE
{draft.get("source", "Google Trends South Africa")}

==================================================
NARRATION SCRIPT
==================================================

{script}

==================================================
CAPCUT SCENE PLAN
==================================================

SCENE 1 - HOOK
Duration: 0:00-0:20

On-screen text:
"{topic}"

Visual:
Use relevant royalty-free footage, screenshots or photographs.

Narration:
Introduce the topic and explain that it is currently trending.

--------------------------------------------------

SCENE 2 - WHAT IS HAPPENING
Duration: 0:20-1:00

On-screen text:
"What's happening?"

Visual:
Use 1-2 relevant visuals.

Narration:
Explain the basic confirmed information surrounding the topic.

--------------------------------------------------

SCENE 3 - WHY IT IS TRENDING
Duration: 1:00-2:00

On-screen text:
"Why is everyone searching?"

Visual:
Use relevant footage, screenshots or graphics.

Narration:
Explain the known reason for the increase in search interest.

--------------------------------------------------

SCENE 4 - KEY DETAILS
Duration: 2:00-3:30

On-screen text:
"Key details"

Visual:
Use supporting visuals.

Narration:
Present the most important confirmed details.

--------------------------------------------------

SCENE 5 - WHAT TO WATCH
Duration: 3:30-4:30

On-screen text:
"What happens next?"

Visual:
Use relevant background footage.

Narration:
Explain what viewers should watch for as the story develops.

--------------------------------------------------

SCENE 6 - OUTRO
Duration: 4:30-5:00+

On-screen text:
"TrendPulse Daily"

Visual:
Simple branded ending.

Narration:
That's the latest TrendPulse Daily update.
Subscribe for more daily trending topics.

==================================================
YOUTUBE METADATA
==================================================

TITLE
{topic} — Why Everyone Is Searching For It Right Now

DESCRIPTION
{topic} is currently trending in South Africa.

In this TrendPulse Daily update, we look at what is driving interest in this topic
and the key information viewers should know.

Information should always be checked against current reliable sources before publication.

Subscribe to TrendPulse Daily for daily trending topics and updates.

HASHTAGS
#TrendPulseDaily
#Trending
#SouthAfrica
#{topic.replace(" ", "")}

==================================================
CAPCUT CHECKLIST
==================================================

[ ] Create 16:9 project
[ ] Add opening title
[ ] Add narration
[ ] Add relevant visuals
[ ] Add captions
[ ] Add background music at low volume
[ ] Check copyright/licensing
[ ] Watch the complete video
[ ] Export MP4
[ ] Upload to YouTube
[ ] Add YouTube title
[ ] Add description
[ ] Add hashtags
[ ] Add thumbnail
"""


    return pack


# ============================================================
# HEADER
# ============================================================

st.title("📈 TrendPulse Daily")

st.caption(
    "Daily trend discovery, approval and free video production workflow"
)


# ============================================================
# GOOGLE TRENDS IMPORT
# ============================================================

st.subheader("🇿🇦 South Africa Google Trends")

st.write(
    "Import the latest trending searches from Google Trends into your Approval Queue."
)

if st.button("🔄 GET LATEST GOOGLE TRENDS", width="stretch"):

    imported_count = import_google_trends()

    if imported_count > 0:
        st.success(
            f"{imported_count} new trending topic(s) added to the Approval Queue."
        )
    else:
        st.info(
            "No new trends were added. The current trends may already be in the queue."
        )

    st.rerun()


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "Approval Queue",
    "Trends",
    "Analytics",
    "Settings"
])


# ============================================================
# APPROVAL QUEUE
# ============================================================

with tab1:

    st.header("Approval Queue")

    drafts = database.get("drafts", [])

    if not drafts:
        st.info("No drafts are currently waiting for approval.")

    else:

        for index, draft in enumerate(drafts):

            if not isinstance(draft, dict):
                continue

            title = get_title(draft)
            status = get_status(draft)

            # ------------------------------------------------
            # STATUS BADGE
            # ------------------------------------------------

            if status == "Approved":
                badge = "🟢 Approved"
            elif status == "Rejected":
                badge = "🔴 Rejected"
            else:
                badge = "🟡 Draft"

            st.markdown(f"### {title}")
            st.write(f"**Status:** {badge}")

            col1, col2, col3 = st.columns(3)

            # ------------------------------------------------
            # APPROVE
            # ------------------------------------------------

            with col1:

                if st.button(
                    "✅ APPROVE",
                    key=f"approve_{draft.get('id', index)}",
                    width="stretch"
                ):

                    draft["status"] = "Approved"

                    if not draft.get("script"):
                        draft["script"] = create_script(title)

                    database["metrics"]["approved"] = (
                        database["metrics"].get("approved", 0) + 1
                    )

                    save_database(database)

                    st.success(f"{title} approved.")
                    st.rerun()

            # ------------------------------------------------
            # REJECT
            # ------------------------------------------------

            with col2:

                if st.button(
                    "❌ REJECT",
                    key=f"reject_{draft.get('id', index)}",
                    width="stretch"
                ):

                    draft["status"] = "Rejected"

                    database["metrics"]["rejected"] = (
                        database["metrics"].get("rejected", 0) + 1
                    )

                    save_database(database)

                    st.warning(f"{title} rejected.")
                    st.rerun()

            # ------------------------------------------------
            # CAPCUT PACK
            # ------------------------------------------------

            with col3:

                if st.button(
                    "🎬 PREPARE CAPCUT PACK",
                    key=f"capcut_{draft.get('id', index)}",
                    width="stretch"
                ):

                    if not draft.get("script"):
                        draft["script"] = create_script(title)

                    pack = create_production_pack(draft)

                    st.session_state[
                        f"production_pack_{draft.get('id', index)}"
                    ] = pack

                    save_database(database)

            # ------------------------------------------------
            # DOWNLOAD PACK
            # ------------------------------------------------

            pack_key = f"production_pack_{draft.get('id', index)}"

            if pack_key in st.session_state:

                st.success("Video production pack is ready.")

                st.download_button(
                    label="⬇️ DOWNLOAD VIDEO PRODUCTION PACK",
                    data=st.session_state[pack_key],
                    file_name=f"TrendPulse_{draft.get('id', index)}_CapCut_Pack.txt",
                    mime="text/plain",
                    key=f"download_{draft.get('id', index)}",
                    width="stretch"
                )

                with st.expander("Preview Production Pack"):

                    st.text(
                        st.session_state[pack_key]
                    )

            # ------------------------------------------------
            # DRAFT DETAILS
            # ------------------------------------------------

            with st.expander("View draft details"):

                st.json(draft)

            st.divider()


# ============================================================
# TRENDS
# ============================================================

with tab2:

    st.header("Live Trends")

    live_trends = fetch_google_trends()

    if live_trends:

        for trend in live_trends[:10]:

            st.write(
                f"**{trend['title']}**"
            )

            st.caption(
                f"Time: {trend.get('time', '')} | "
                f"Traffic: {trend.get('traffic', '')}"
            )

    else:

        st.info(
            "Click GET LATEST GOOGLE TRENDS to load current trends."
        )

    st.divider()

    st.header("Imported Trend History")

    if database.get("topics"):

        for topic in database["topics"]:

            st.write(
                f"**{topic.get('title', '')}**"
            )

            st.caption(
                f"Source: {topic.get('source', '')} | "
                f"Time: {topic.get('time', '')} | "
                f"Traffic: {topic.get('traffic', '')}"
            )

    else:

        st.info("No imported trends yet.")


# ============================================================
# ANALYTICS
# ============================================================

with tab3:

    st.header("Analytics")

    metrics = database.get("metrics", {})

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Videos Published",
            metrics.get("videos_published", 0)
        )

    with col2:
        st.metric(
            "Approved",
            metrics.get("approved", 0)
        )

    with col3:
        st.metric(
            "Rejected",
            metrics.get("rejected", 0)
        )


# ============================================================
# SETTINGS
# ============================================================

with tab4:

    st.header("Settings")

    st.write("### Current workflow")

    st.write(
        "Google Trends → TrendPulse → Approval → "
        "Free CapCut Production Pack → CapCut → YouTube"
    )

    st.write("### Video format")

    st.write(
        "16:9 YouTube videos, approximately 3–6 minutes."
    )

    st.write("### AI video generation")

    st.write(
        "Paid OpenAI video generation is not required."
    )

    st.write(
        "TrendPulse prepares the topic, script, metadata and CapCut production plan. "
        "The video can then be assembled using CapCut's free tools and appropriately "
        "licensed media."
    )

    st.write("### Google Trends")

    st.write(
        "TrendPulse is configured for South Africa (ZA)."
    )

    st.write(
        "The Approval Queue now receives newly imported Google Trends topics automatically."
    )
