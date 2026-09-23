import streamlit as st
from pathlib import Path
import json
import pandas as pd

DB = Path("trendpulse_data.json")


def load():
    if DB.exists():
        return json.loads(DB.read_text())
    return {
        "drafts": [],
        "topics": [],
        "metrics": []
    }


def save(data):
    DB.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )


def get_google_trends():
    try:
        import requests
        import xml.etree.ElementTree as ET

        url = "https://trends.google.com/trending/rss?geo=ZA"

        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        root = ET.fromstring(response.text)

        topics = []

        for item in root.findall(".//item")[:10]:
            title = item.findtext("title")

            if title:
                topics.append({
                    "Topic": title,
                    "Niche": "Trending topics",
                    "Interest": "Trending",
                    "Competition": "Unknown"
                })

        return topics

    except Exception:
        return []


data = load()


if not data["drafts"]:
    data["drafts"] = [
        {
            "id": 1,
            "title": "Example TrendPulse Daily draft",
            "niche": "Trending topics",
            "status": "Awaiting approval",
            "scheduled_for": "20:00 SAST",
            "copyright_check": "Pending",
            "script": (
                "Placeholder draft. Live trend research "
                "and rendering will be added in the next build."
            )
        }
    ]

    save(data)


st.set_page_config(
    page_title="TrendPulse Daily",
    layout="wide"
)

st.title("TrendPulse Daily")

st.caption(
    "Automated content control • "
    "08:00 SAST review • "
    "Human approval required"
)


approval_tab, trends_tab, analytics_tab, settings_tab = st.tabs(
    [
        "Approval Queue",
        "Trends",
        "Analytics",
        "Settings"
    ]
)


with approval_tab:

    st.header("Daily approval queue")

    st.info(
        "Drafts are intended to be ready by 08:00 SAST. "
        "Nothing publishes without approval."
    )

    for draft in data["drafts"]:

        with st.container(border=True):

            st.subheader(draft["title"])

            st.write(
                "Niche:",
                draft["niche"]
            )

            st.write(
                "Status:",
                draft["status"]
            )

            st.write(
                "Scheduled time:",
                draft["scheduled_for"]
            )

            st.write(
                "Copyright check:",
                draft["copyright_check"]
            )

            st.text_area(
                "Script preview",
                draft["script"],
                key=f"script_{draft['id']}"
            )

            approve_col, reject_col = st.columns(2)

            if approve_col.button(
                "APPROVE & SCHEDULE",
                key=f"approve_{draft['id']}"
            ):

                draft["status"] = (
                    "Approved — awaiting YouTube integration"
                )

                save(data)

                st.success(
                    "Approval recorded locally."
                )

                st.rerun()

            if reject_col.button(
                "REJECT",
                key=f"reject_{draft['id']}"
            ):

                draft["status"] = (
                    "Rejected — needs revision"
                )

                save(data)

                st.warning(
                    "Draft rejected."
                )

                st.rerun()


with trends_tab:

    st.header("Trending topics")

    st.write(
        "TrendPulse uses Google Trends to identify "
        "current South African search trends."
    )

    if st.button(
        "REFRESH GOOGLE TRENDS",
        key="refresh_trends"
    ):

        with st.spinner(
            "Getting current Google Trends..."
        ):

            new_topics = get_google_trends()

        if new_topics:

            data["topics"] = new_topics

            save(data)

            st.success(
                "Google Trends refreshed successfully."
            )

        else:

            st.error(
                "Google Trends could not be loaded right now. "
                "Try again in a few minutes."
            )

    if data["topics"]:

        st.dataframe(
            pd.DataFrame(data["topics"]),
            use_container_width=True
        )

    else:

        st.info(
            "Click REFRESH GOOGLE TRENDS "
            "to load current South African trends."
        )


with analytics_tab:

    st.header("Analytics")

    st.info(
        "YouTube Analytics connection will populate "
        "views, watch time, retention and revenue "
        "when available."
    )

    if data["metrics"]:

        st.dataframe(
            pd.DataFrame(data["metrics"]),
            use_container_width=True
        )

    else:

        st.dataframe(
            pd.DataFrame(
                columns=[
                    "Video",
                    "Views",
                    "Watch time",
                    "Revenue"
                ]
            ),
            use_container_width=True
        )


with settings_tab:

    st.header("Settings")

    st.write(
        "Approval deadline: 08:00 SAST"
    )

    st.write(
        "Default publishing time: 20:00 SAST"
    )

    st.write(
        "Publishing mode: Manual approval required"
    )

    st.write(
        "Trend provider: Google Trends"
    )

    st.write(
        "Channel: TrendPulse Daily"
    )
