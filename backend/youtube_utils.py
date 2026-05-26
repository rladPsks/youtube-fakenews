import os
import re
import glob
import subprocess
from pathlib import Path


PROXY_URL = os.getenv(
    "PROXY_URL",
    "http://qllyfnqs-kr-1:lnpl06rmksdc@p.webshare.io:80"
)


def extract_video_id(url: str) -> str:
    patterns = [
        r"v=([^&]+)",
        r"youtu\.be/([^?&]+)",
        r"shorts/([^?&]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return url.strip()


def clean_vtt(vtt_path: str) -> str:
    with open(vtt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cleaned = []
    prev = None

    for line in lines:
        line = line.strip()

        if not line:
            continue
        if line.startswith("WEBVTT"):
            continue
        if "-->" in line:
            continue
        if line.startswith("Kind:") or line.startswith("Language:"):
            continue

        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"&nbsp;", " ", line)
        line = line.strip()

        if line and line != prev:
            cleaned.append(line)
            prev = line

    return " ".join(cleaned).strip()


def get_transcript(video_id: str) -> str:
    try:
        tmp_dir = Path("tmp_subs")
        tmp_dir.mkdir(exist_ok=True)

        video_url = f"https://www.youtube.com/watch?v={video_id}"

        cmd = [
            "yt-dlp",
            "--proxy", PROXY_URL,
            "--force-overwrites",
            "--write-auto-sub",
            "--write-sub",
            "--sub-lang", "ko,en",
            "--skip-download",
            "-o", str(tmp_dir / "%(id)s.%(ext)s"),
            video_url,
        ]

        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        print("[YTDLP STDOUT]", result.stdout, flush=True)
        print("[YTDLP STDERR]", result.stderr, flush=True)

        vtt_files = glob.glob(str(tmp_dir / f"{video_id}*.vtt"))

        if not vtt_files:
            raise RuntimeError("NO_VTT_SUBTITLE_FOUND")

        ko_files = [f for f in vtt_files if f.endswith(".ko.vtt")]
        selected = ko_files[0] if ko_files else vtt_files[0]

        text = clean_vtt(selected)

        if not text:
            raise RuntimeError("NO_TRANSCRIPT_EMPTY")

        return text

    except subprocess.CalledProcessError as e:
        print("[YTDLP TRANSCRIPT ERROR]", flush=True)
        print("returncode:", e.returncode, flush=True)
        print("cmd:", e.cmd, flush=True)
        print("stdout:", e.stdout, flush=True)
        print("stderr:", e.stderr, flush=True)
        raise RuntimeError(f"NO_TRANSCRIPT: {e.stderr}")

    except Exception as e:
        print("[YTDLP UNKNOWN ERROR]", repr(e), flush=True)
        raise RuntimeError(f"NO_TRANSCRIPT: {repr(e)}")