import re
from youtube_transcript_api import YouTubeTranscriptApi


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


def get_transcript(video_id: str) -> str:
    try:
        api = YouTubeTranscriptApi()

        transcript = api.fetch(
            video_id,
            languages=["ko", "en"]
        )

        text = " ".join([item.text for item in transcript]).strip()

        if not text:
            raise RuntimeError("NO_TRANSCRIPT_EMPTY")

        return text

    except Exception as e:
        print("[TRANSCRIPT ERROR]", repr(e), flush=True)
        raise RuntimeError(f"NO_TRANSCRIPT: {repr(e)}")