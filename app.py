import streamlit as st
from pathlib import Path
import json
import requests
import xml.etree.ElementTree as ET
import subprocess
import shutil
from datetime import datetime
import pickle

st.set_page_config(page_title="TrendPulse Daily", page_icon="📈", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
DB = BASE_DIR / "trendpulse_data.json"
VIDEO_DIR = BASE_DIR / "trendpulse_videos"
AUDIO_DIR = BASE_DIR / "trendpulse_audio"
CREDS_DIR = BASE_DIR / "creds"

VIDEO_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)
CREDS_DIR.mkdir(exist_ok=True)

def load():
    if not DB.exists():
        return {"drafts": [], "topics": [], "metrics": []}
    try:
        data = json.loads(DB.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            data = {}
        data.setdefault("drafts", [])
        data.setdefault("topics", [])
        data.setdefault("metrics", [])
        
        for draft in data["drafts"]:
            if "topic" not in draft:
                draft["topic"] = draft.get("title", "Untitled")
            if "title" not in draft:
                draft["title"] = draft["topic"]
            if "script" not in draft:
                draft["script"] = ""
            if "status" not in draft:
                draft["status"] = "Awaiting approval"
            if "scheduled" not in draft:
                draft["scheduled"] = "20:00 SAST"
            if "created" not in draft:
                draft["created"] = ""
            if "audio" not in draft:
                draft["audio"] = ""
            if "video" not in draft:
                draft["video"] = ""
        
        return data
    except Exception:
        return {"drafts": [], "topics": [], "metrics": []}

def save(data):
    DB.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

data = load()
save(data)

def get_trends():
    url = "https://trends.google.com/trending/rss?geo=ZA"
    try:
        response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        root = ET.fromstring(response.content)
        topics = []
        for item in root.findall(".//item"):
            title = item.findtext("title")
            if title:
                topics.append(title.strip())
        return topics[:20]
    except Exception as error:
        st.error("Could not load Google Trends.")
        return []

def make_script(topic):
    return f"""Welcome to TrendPulse Daily.

Today's trending topic is {topic}.

This topic is currently receiving search interest from people in South Africa.

In this video, we look at what people are searching for and why this topic is receiving attention.

Search trends can change quickly.

Trending searches show what people are looking for, but they do not automatically confirm that every claim or report surrounding a topic is true.

For important developments, viewers should always check reliable and confirmed information.

We will continue monitoring this topic and provide updates when reliable information becomes available.

That is today's TrendPulse Daily update.

Subscribe to TrendPulse Daily for more daily trending topics from South Africa."""

def create_draft(topic):
    ids = []
    for draft in data["drafts"]:
        try:
            ids.append(int(draft.get("id", 0)))
        except Exception:
            pass
    draft_id = max(ids) + 1 if ids else 1
    draft = {
        "id": draft_id,
        "topic": topic,
        "title": topic,
        "script": make_script(topic),
        "status": "Awaiting approval",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled": "20:00 SAST",
        "audio": "",
        "video": ""
    }
    data["drafts"].append(draft)
    save(data)

def create_voice(script, draft_id):
    audio_path = AUDIO_DIR / f"trendpulse_{draft_id}.wav"
    text_path = AUDIO_DIR / f"trendpulse_{draft_id}.txt"
    text_path.write_text(script, encoding="utf-8")
    
    powershell_script = f"""
Add-Type -AssemblyName System.Speech
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speaker.Rate = 0
$speaker.Volume = 100
$speaker.SetOutputToWaveFile("{audio_path}")
$text = Get-Content -Raw -Encoding UTF8 "{text_path}"
$speaker.Speak($text)
$speaker.Dispose()
"""
    
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", powershell_script],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        if not audio_path.exists():
            raise RuntimeError("Voiceover file was not created.")
        return str(audio_path)
    except Exception as error:
        st.error("Voiceover creation failed.")
        return None

def create_video(script, topic, audio_path, draft_id):
    output_path = VIDEO_DIR / f"trendpulse_draft_{draft_id}.mp4"
    text_path = VIDEO_DIR / f"trendpulse_text_{draft_id}.txt"
    
    screen_text = topic + "\n\nTRENDING IN SOUTH AFRICA\n\nTrendPulse Daily"
    text_path.write_text(screen_text, encoding="utf-8")
    
    windows_font = Path("C:/Windows/Fonts/arial.ttf")
    local_font = VIDEO_DIR / "arial.ttf"
    
    try:
        if windows_font.exists():
            shutil.copyfile(windows_font, local_font)
    except Exception:
        pass
    
    relative_text = text_path.relative_to(BASE_DIR).as_posix()
    
    font_option = ""
    if local_font.exists():
        relative_font = local_font.relative_to(BASE_DIR).as_posix()
        font_option = f"fontfile='{relative_font}':"
    
    video_filter = (
        "drawtext=" + font_option +
        f"textfile='{relative_text}':" +
        "fontcolor=white:" +
        "fontsize=64:" +
        "line_spacing=18:" +
        "x=(w-text_w)/2:" +
        "y=(h-text_h)/2:" +
        "box=1:" +
        "boxcolor=black@0.45:" +
        "boxborderw=30"
    )
    
    command = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "color=c=0x16213E:s=1920x1080:r=30",
        "-i", audio_path,
        "-vf", video_filter,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(output_path)
    ]
    
    try:
        result = subprocess.run(
            command,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True
        )
