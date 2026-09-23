import streamlit as st
from pathlib import Path
import json
import os
import re
import tempfile

import pandas as pd
from openai import OpenAI

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build


# ============================================================
# APP CONFIG
# ============================================================

st.set_page_config(
    page_title="TrendPulse Daily",
    layout="wide"
)


DB = Path("trendpulse_data.json")

VIDEO_DIR = Path("generated_videos")
VIDEO_DIR.mkdir(exist_ok=True)

ASSET_DIR = Path("generated_assets")
ASSET_DIR.mkdir(exist_ok=True)


YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


REDIRECT_URI = (
    "https://8spy6syfwejab9zzb4sedh.streamlit.app"
)


# ============================================================
# DATABASE
# ============================================================

def load():

    if DB.exists():

        try:
            return json.loads(
                DB.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:
            pass


    return {
        "drafts": [],
        "topics": [],
        "metrics": []
    }


def save(data):

    DB.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


# ============================================================
# OPENAI
# ============================================================

def get_openai_client():

    try:

        api_key = st.secrets["openai"]["api_key"]

    except Exception:

        return None


    if not api_key:

        return None


    return OpenAI(
        api_key=api_key
    )


# ============================================================
# GOOGLE TRENDS
# ============================================================

def get_google_trends():

    try:

        import requests
        import xml.etree.ElementTree as ET


        url = (
            "https://trends.google.com/"
            "trending/rss?geo=ZA"
        )


        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )


        response.raise_for_status()


        root = ET.fromstring(
            response.text
        )


        topics = []


        for item in root.findall(".//item")[:10]:

            title = item.findtext(
                "title"
            )


            if title:

                topics.append(
                    {
                        "Topic": title,
                        "Niche": "Trending topics",
                        "Interest": "Trending",
                        "Competition": "Unknown"
                    }
                )


        return topics


    except Exception:

        return []


# ============================================================
# DRAFT CREATION
# ============================================================

def create_trend_draft(
    topic,
    draft_id
):

    return {

        "id": draft_id,

        "title": (
            f"{topic}: What South Africans "
            "Need to Know"
        ),

        "niche": "Trending topics",

        "status": "Awaiting approval",

        "scheduled_for": "20:00 SAST",

        "copyright_check": "Pending",

        "script": (
            f"Today's trending topic is {topic}.\n\n"
            f"In this video, we explore what {topic} "
            "means, why people are discussing it, "
            "and the key facts viewers should know.\n\n"
            "This draft requires review before publishing."
        ),

        "video_path": None,

        "audio_path": None,

        "visuals": []

    }


# ============================================================
# AI SCRIPT GENERATION
# ============================================================

def generate_ai_script(
    topic,
    client
):

    prompt = f"""
Create a YouTube news/explainer script about:

{topic}

Target audience:
South African viewers.

Video length:
Approximately 3 to 6 minutes.

Format:
16:9 normal YouTube video, NOT a Short.

Requirements:

- Start with a strong but factual hook.
- Explain what is happening.
- Explain why people are talking about it.
- Give relevant background.
- Clearly distinguish confirmed facts from uncertainty.
- Do not invent facts.
- Do not make unsupported accusations.
- Use natural spoken language.
- Keep the pacing engaging.
- Include a short conclusion.
- Include a natural call to subscribe.
- Do not include stage directions.
- Do not include markdown headings.
- Do not include citations.
- Target approximately 750 to 950 words.

Return only the finished narration script.
"""


    response = client.responses.create(

        model="gpt-5.6-luna",

        input=prompt
    )


    return response.output_text.strip()


# ============================================================
# SCENE PLANNING
# ============================================================

def create_scene_prompts(
    topic,
    script,
    client
):

    prompt = f"""
Create 5 visual scene prompts for a YouTube video.

Topic:
{topic}

Narration:
{script}

The video is for a South African audience.

Return exactly 5 numbered visual prompts.

Each prompt should describe:
- The main subject
- The environment
- The composition
- The mood
- A realistic documentary/news visual style
- 16:9 landscape composition

Do not request text inside the image.

Do not use logos or copyrighted characters.

Keep the visuals factual and appropriate for a general audience.
"""


    response = client.responses.create(

        model="gpt-5.6-luna",

        input=prompt
    )


    text = response.output_text.strip()


    prompts = []


    for line in text.splitlines():

        line = line.strip()


        if not line:
            continue


        line = re.sub(
            r"^\d+[\.\):\-]\s*",
            "",
            line
        )


        if len(line) > 30:

            prompts.append(line)


    return prompts[:5]


# ============================================================
# AI IMAGE GENERATION
# ============================================================

def generate_visuals(
    topic,
    scene_prompts,
    client,
    draft_id
):

    image_paths = []


    for index, scene in enumerate(
        scene_prompts,
        start=1
    ):

        prompt = f"""
Create a high-quality documentary-style
YouTube visual for this topic:

{topic}

Scene:
{scene}

Requirements:

- 16:9 landscape composition.
- Photorealistic documentary/news style.
- Cinematic but factual.
- Suitable for a general YouTube audience.
- No written text.
- No logos.
- No watermarks.
"""


        result = client.images.generate(

            model="gpt-image-2",

            prompt=prompt,

            size="1536x1024"
        )


        image_data = result.data[0]


        if getattr(
            image_data,
            "b64_json",
            None
        ):

            import base64


            image_bytes = base64.b64decode(
                image_data.b64_json
            )


            image_path = (
                ASSET_DIR
                / f"draft_{draft_id}_scene_{index}.png"
            )


            image_path.write_bytes(
                image_bytes
            )


            image_paths.append(
                str(image_path)
            )


    return image_paths


# ============================================================
# AI VOICE GENERATION
# ============================================================

def generate_voice(
    script,
    client,
    draft_id
):

    audio_path = (
        ASSET_DIR
        / f"draft_{draft_id}_narration.mp3"
    )


    # Keep requests manageable if a script becomes very long.
    chunks = []


    words = script.split()


    current = []


    for word in words:

        current.append(word)


        if len(current) >= 450:

            chunks.append(
                " ".join(current)
            )

            current = []


    if current:

        chunks.append(
            " ".join(current)
        )


    audio_parts = []


    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        part_path = (
            ASSET_DIR
            / f"draft_{draft_id}_voice_{index}.mp3"
        )


        with client.audio.speech.with_streaming_response.create(

            model="gpt-4o-mini-tts",

            voice="marin",

            input=chunk,

            response_format="mp3"
        ) as response:

            response.stream_to_file(
                part_path
            )


        audio_parts.append(
            part_path
        )


    if len(audio_parts) == 1:

        audio_parts[0].replace(
            audio_path
        )

        return str(audio_path)


    # Combine audio parts with pydub.
    from pydub import AudioSegment


    combined = AudioSegment.empty()


    for part in audio_parts:

        combined += AudioSegment.from_file(
            part,
            format="mp3"
        )


    combined.export(
        audio_path,
        format="mp3"
    )


    return str(audio_path)


# ============================================================
# VIDEO ASSEMBLY
# ============================================================

def create_video(
    image_paths,
    audio_path,
    draft_id
):

    from moviepy import (
        ImageClip,
        AudioFileClip,
        concatenate_videoclips
    )


    audio = AudioFileClip(
        audio_path
    )


    total_duration = audio.duration


    if not image_paths:

        raise ValueError(
            "No AI visuals were generated."
        )


    scene_duration = (
        total_duration
        / len(image_paths)
    )


    clips = []


    for image_path in image_paths:

        clip = (
            ImageClip(image_path)
            .with_duration(scene_duration)
            .resized(
                width=1920
            )
        )


        clips.append(
            clip
        )


    video = concatenate_videoclips(
        clips,
        method="compose"
    )


    video = video.with_audio(
        audio
    )


    output_path = (
        VIDEO_DIR
        / f"trendpulse_draft_{draft_id}.mp4"
    )


    video.write_videofile(

        str(output_path),

        fps=24,

        codec="libx264",

        audio_codec="aac",

        preset="medium",

        logger=None
    )


    video.close()

    audio.close()


    return str(output_path)


# ============================================================
# COMPLETE AI VIDEO PIPELINE
# ============================================================

def generate_complete_video(
    draft,
    client
):

    topic = draft["title"]


    # --------------------------------------------------------
    # 1. Generate longer YouTube script
    # --------------------------------------------------------

    script = generate_ai_script(
        topic,
        client
    )


    # --------------------------------------------------------
    # 2. Create scene prompts
    # --------------------------------------------------------

    scene_prompts = create_scene_prompts(
        topic,
        script,
        client
    )


    if not scene_prompts:

        raise RuntimeError(
            "The AI could not create visual scenes."
        )


    # --------------------------------------------------------
    # 3. Generate AI visuals
    # --------------------------------------------------------

    image_paths = generate_visuals(
        topic,
        scene_prompts,
        client,
        draft["id"]
    )


    if not image_paths:

        raise RuntimeError(
            "No AI images were generated."
        )


    # --------------------------------------------------------
    # 4. Generate AI narration
    # --------------------------------------------------------

    audio_path = generate_voice(
        script,
        client,
        draft["id"]
    )


    # --------------------------------------------------------
    # 5. Assemble MP4
    # --------------------------------------------------------

    video_path = create_video(
        image_paths,
        audio_path,
        draft["id"]
    )


    return {
        "script": script,
        "video_path": video_path,
        "audio_path": audio_path,
        "visuals": image_paths
    }


# ============================================================
# YOUTUBE OAUTH
# ============================================================

def create_youtube_flow():

    client_config = {

        "web": {

            "client_id": (
                st.secrets["youtube"]["client_id"]
            ),

            "client_secret": (
                st.secrets["youtube"]["client_secret"]
            ),

            "auth_uri": (
                "https://accounts.google.com/"
                "o/oauth2/auth"
            ),

            "token_uri": (
                "https://oauth2.googleapis.com/token"
            )
        }
    }


    flow = Flow.from_client_config(

        client_config,

        scopes=YOUTUBE_SCOPES,

        autogenerate_code_verifier=False
    )


    flow.redirect_uri = REDIRECT_URI


    return flow


# ============================================================
# SESSION STATE
# ============================================================

if "trendpulse_data" not in st.session_state:

    st.session_state.trendpulse_data = load()


data = st.session_state.trendpulse_data


if "youtube_connected" not in st.session_state:

    st.session_state.youtube_connected = False


if "youtube_channel" not in st.session_state:

    st.session_state.youtube_channel = None


if "youtube_credentials" not in st.session_state:

    st.session_state.youtube_credentials = None


# ============================================================
# DEFAULT DRAFT
# ============================================================

if not data["drafts"]:

    data["drafts"] = [

        {
            "id": 1,

            "title":
                "Example TrendPulse Daily draft",

            "niche":
                "Trending topics",

            "status":
                "Awaiting approval",

            "scheduled_for":
                "20:00 SAST",

            "copyright_check":
                "Pending",

            "script":
                "Placeholder draft. Select a live trend "
                "to create a new video draft.",

            "video_path":
                None,

            "audio_path":
                None,

            "visuals":
                []
        }
    ]


    save(data)


# ============================================================
# HEADER
# ============================================================

st.title(
    "TrendPulse Daily"
)


st.caption(
    "Automated content control • "
    "08:00 SAST review • "
    "Human approval required"
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

    st.header(
        "Daily approval queue"
    )


    st.info(
        "Drafts are intended to be ready by "
        "08:00 SAST. Nothing publishes without approval."
    )


    for draft in data["drafts"]:

        with st.container(
            border=True
        ):

            st.subheader(
                draft["title"]
            )


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


            # ------------------------------------------------
            # AI VIDEO GENERATION
            # ------------------------------------------------

            if draft.get("video_path"):

                st.success(
                    "AI video generated."
                )


                video_file = Path(
                    draft["video_path"]
                )


                if video_file.exists():

                    st.video(
                        str(video_file)
                    )


            else:

                client = get_openai_client()


                if client:

                    if st.button(

                        "GENERATE AI VIDEO",

                        key=f"generate_video_{draft['id']}"
                    ):

                        try:

                            with st.spinner(
                                "Creating script, AI visuals, "
                                "voice narration and 16:9 video..."
                            ):

                                result = (
                                    generate_complete_video(
                                        draft,
                                        client
                                    )
                                )


                            draft["script"] = (
                                result["script"]
                            )


                            draft["video_path"] = (
                                result["video_path"]
                            )


                            draft["audio_path"] = (
                                result["audio_path"]
                            )


                            draft["visuals"] = (
                                result["visuals"]
                            )


                            draft["status"] = (
                                "Video ready — awaiting approval"
                            )


                            save(data)


                            st.success(
                                "AI video created successfully."
                            )


                            st.rerun()


                        except Exception as error:

                            st.error(
                                "AI video generation failed: "
                                f"{error}"
                            )

                else:

                    st.warning(
                        "OpenAI is not configured. "
                        "Check Streamlit Secrets."
                    )


            # ------------------------------------------------
            # SCRIPT
            # ------------------------------------------------

            st.text_area(

                "Script preview",

                draft["script"],

                key=f"script_{draft['id']}",

                height=220
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


# ============================================================
# TRENDS
# ============================================================

with trends_tab:

    st.header(
        "Trending topics"
    )


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

            new_topics = (
                get_google_trends()
            )


        if new_topics:

            data["topics"] = new_topics


            save(data)


            st.success(
                "Google Trends refreshed successfully."
            )


            st.rerun()


        else:

            st.error(
                "Google Trends could not be loaded right now. "
                "Try again in a few minutes."
            )


    if data["topics"]:

        st.dataframe(

            pd.DataFrame(
                data["topics"]
            ),

            use_container_width=True
        )


        st.subheader(
            "Create video draft"
        )


        if st.button(

            "CREATE DRAFT FROM TOP TREND",

            key="create_trend_draft"
        ):

            next_id = max(

                [
                    draft["id"]
                    for draft in data["drafts"]
                ],

                default=0

            ) + 1


            top_topic = (
                data["topics"][0]["Topic"]
            )


            new_draft = (
                create_trend_draft(
                    top_topic,
                    next_id
                )
            )


            data["drafts"].append(
                new_draft
            )


            save(data)


            st.success(
                f"Draft created for: {top_topic}"
            )


            st.info(
                "Open the Approval Queue tab "
                "to generate the AI video."
            )


    else:

        st.info(
            "Click REFRESH GOOGLE TRENDS "
            "to load current South African trends."
        )


# ============================================================
# ANALYTICS
# ============================================================

with analytics_tab:

    st.header(
        "Analytics"
    )


    st.info(
        "YouTube Analytics connection will populate "
        "views, watch time, retention and revenue "
        "when available."
    )


    if data["metrics"]:

        st.dataframe(

            pd.DataFrame(
                data["metrics"]
            ),

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


# ============================================================
# SETTINGS
# ============================================================

with settings_tab:

    st.header(
        "Settings"
    )


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
        "Video format: 16:9 YouTube"
    )


    st.write(
        "Target length: 3–6 minutes"
    )


    st.write(
        "Voice: AI narration"
    )


    st.write(
        "Visuals: AI-generated"
    )


    st.write(
        "Trend provider: Google Trends"
    )


    st.write(
        "Channel: TrendPulse Daily"
    )


    st.divider()


    st.subheader(
        "YouTube connection"
    )


    query_params = st.query_params


    if "code" in query_params:

        try:

            flow = create_youtube_flow()


            flow.fetch_token(
                code=query_params["code"]
            )


            credentials = (
                flow.credentials
            )


            youtube = build(

                "youtube",

                "v3",

                credentials=credentials
            )


            channel_response = (

                youtube.channels()

                .list(

                    part="snippet",

                    mine=True

                )

                .execute()
            )


            channels = (
                channel_response.get(
                    "items",
                    []
                )
            )


            if channels:

                channel = channels[0]


                st.session_state.youtube_credentials = (
                    credentials
                )


                st.session_state.youtube_connected = (
                    True
                )


                st.session_state.youtube_channel = (
                    channel["snippet"]["title"]
                )


                st.query_params.clear()


                st.success(
                    "YouTube connected successfully."
                )


                st.rerun()


            else:

                st.error(
                    "Google authentication succeeded, "
                    "but no YouTube channel was found."
                )


        except Exception as error:

            st.error(
                f"YouTube connection failed: {error}"
            )


    if st.session_state.youtube_connected:

        st.success(
            "YouTube connected"
        )


        st.write(
            "Channel:",
            st.session_state.youtube_channel
        )


    else:

        if st.button(

            "CONNECT YOUTUBE",

            key="connect_youtube"
        ):

            try:

                flow = create_youtube_flow()


                authorization_url, state = (

                    flow.authorization_url(

                        access_type="offline",

                        include_granted_scopes="true",

                        prompt="consent"

                    )
                )


                st.link_button(

                    "AUTHORIZE TRENDPULSE DAILY ON GOOGLE",

                    authorization_url
                )


                st.info(

                    "Click the authorization button above "
                    "and sign in with the Google account "
                    "that owns your YouTube channel."

                )


            except Exception as error:

                st.error(

                    f"Could not start YouTube connection: "
                    f"{error}"

                )
