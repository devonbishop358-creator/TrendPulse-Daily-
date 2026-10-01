import streamlit as st
from pathlib import Path
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import subprocess
import pyttsx3
from PIL import Image, ImageDraw, ImageFont
import os

st.set_page_config(page_title="TrendPulse Daily", page_icon="📈", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
DB = BASE_DIR / "trendpulse_data.json"
VIDEO_DIR = BASE_DIR / "trendpulse_videos"
AUDIO_DIR = BASE_DIR / "trendpulse_audio"
IMG_DIR = BASE_DIR / "trendpulse_images"

VIDEO_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)
IMG_DIR.mkdir(exist_ok=True)

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
            draft.setdefault("youtube_url", "")
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
    return f"""Welcome to TrendPulse Daily. Today's trending topic is {topic}. This topic is currently receiving search interest from people in South Africa. In this video, we look at what people are searching for and why this topic is receiving attention. Search trends can change quickly. For important developments, viewers should always check reliable and confirmed information. That is today's TrendPulse Daily update. Subscribe for more daily trending topics from South Africa."""

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
        if audio_path.exists():
            return str(audio_path)
        else:
            st.error("Audio file not created")
            return None
    except Exception as e:
        st.error(f"Voiceover creation failed: {str(e)}")
        return None

def create_video(topic, audio_path, draft_id):
    try:
        if not Path(audio_path).exists():
            st.error("Audio file not found")
            return None
        video_path = VIDEO_DIR / f"trendpulse_{draft_id}.mp4"
        img_path = IMG_DIR / f"trendpulse_{draft_id}.png"
        img = Image.new('RGB', (1920, 1080), color=(22, 33, 62))
        draw = ImageDraw.Draw(img)
        try:
            font_size = 80
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        text = topic
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (1920 - text_width) // 2
        y = (1080 - text_height) // 2
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        draw.text((x, y + 150), "TRENDING IN SOUTH AFRICA", fill=(150, 150, 150), font=font)
        draw.text((x, y + 300), "TrendPulse Daily", fill=(100, 200, 255), font=font)
        img.save(str(img_path))
        cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", audio_path,
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and video_path.exists():
            return str(video_path)
        else:
            st.error("FFmpeg error - install FFmpeg from ffmpeg.org")
            return None
    except Exception as e:
        st.error(f"Video creation failed: {str(e)}")
        return None

st.title("📈 TrendPulse Daily")
st.caption("Daily trend discovery and YouTube monetization")

tab1, tab2, tab3, tab4 = st.tabs(["Approval Queue", "Trends", "Analytics", "Settings"])

with tab1:
    st.header("Approval Queue")
    st.info("Nothing publishes without your approval.")
    if not data["drafts"]:
        st.info("No drafts are waiting for approval.")
    else:
        for draft in reversed(data["drafts"]):
            st.divider()
            topic = draft.get("topic", "Untitled")
