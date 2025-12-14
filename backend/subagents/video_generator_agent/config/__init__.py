# Config module initialization
# Config module initialization
import os
from pathlib import Path

# Default paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
AUDIO_INPUT_PATH = PROJECT_ROOT / "project" / "inputs" / "VoiceOver.wav"
OUTPUT_DIR = PROJECT_ROOT / "human_deliverable"
TEMP_DIR = PROJECT_ROOT / "temp_wan_videos"

# Video generation settings
VIDEO_SETTINGS = {
    'fps': 24,
    'codec': 'libx264',
    'audio_codec': 'aac',
    'resolution': (1920, 1080),
    'style': '2D animated flat design'
}

# Model settings
MODEL_SETTINGS = {
    'wan-2.5': {
        'max_segment_duration': 10,
        'min_segment_duration': 5,
        'api_model': 'wan-video/wan-2.5-t2v'
    }
}


def get_replicate_token():
    """Get Replicate API token from environment"""
    return os.getenv("REPLICATE_API_TOKEN")
