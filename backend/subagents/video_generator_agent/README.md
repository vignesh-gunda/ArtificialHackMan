# Video Generator Agent

A modular video generation agent using the DeepAgents framework for creating 2D animated explainer videos.

## Features

- **2D Animated Video Generation**: Creates flat design, vector-style animated videos
- **Speech-to-Text Integration**: Converts audio to text for content-aware video generation
- **Wan 2.5 AI Model**: Uses Replicate's Wan 2.5 model for AI video generation
- **Content-Aware Segments**: Automatically classifies content and creates appropriate visuals
- **Audio Synchronization**: Matches video duration exactly to audio length

## Structure

```
video_generator_agent/
├── __init__.py                 # Package exports
├── deepagent_subsystem.py      # Main VideoGeneratorAgent class
├── generate_video.py           # CLI entry point
├── config/
│   └── __init__.py             # Configuration settings
├── generator/
│   ├── __init__.py             # Generator exports
│   └── wan_video_generator.py  # Wan 2.5 video generator
└── utils/
    ├── __init__.py             # Utils exports
    └── list_outputs.py         # Video listing utility
```

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r video_generator_agent/requirements.txt

# Or install from project root
pip install -r requirements.txt
```

### Usage

#### CLI Mode
```bash
# Interactive mode
python video_generator_agent/generate_video.py

# Direct Wan 2.5 generation
python video_generator_agent/generate_video.py wan

# List generated videos
python video_generator_agent/generate_video.py --list
```

#### Python API
```python
from video_generator_agent import VideoGeneratorAgent, WanVideoGenerator

# Using the agent
agent = VideoGeneratorAgent()
output_path = agent.generate_video()

# Or directly use the generator
generator = WanVideoGenerator()
output_path = generator.generate_video()
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Replicate API Token (optional - enables AI video generation)
REPLICATE_API_TOKEN=your_token_here

# Speech Recognition Settings (optional)
SPEECH_RECOGNITION_TIMEOUT=10
SPEECH_RECOGNITION_PHRASE_TIMEOUT=5
```

### Video Settings

Default settings in `config/__init__.py`:

- **Resolution**: 1920x1080 (1080p)
- **FPS**: 24
- **Codec**: H.264 (libx264)
- **Audio Codec**: AAC
- **Style**: 2D animated flat design

## Video Generation Workflow

1. **Analyze Audio**: Extract duration from input audio file
2. **Transcribe Speech**: Convert speech to text using Google/Sphinx
3. **Enhance Prompt**: Create 2D animation-focused prompts
4. **Generate Segments**: Create video segments for each content section
5. **Compose Video**: Combine segments with original audio
6. **Cleanup**: Remove temporary files

## Content Types

The generator automatically classifies content and creates appropriate visuals:

- **Introduction**: Company logo and welcome
- **Consultation**: Customer meeting scenes
- **Assessment**: Tree health evaluation
- **Pruning**: Tree trimming operations
- **Stump Removal**: Grinding and removal
- **Planning**: Customized care plans
- **Technology**: Modern equipment showcase
- **Safety**: Safety protocols and equipment
- **Cleanup**: Final cleanup process
- **Call to Action**: Contact information

## Output

Generated videos are saved to:

```
human_deliverable/
└── wan-2.5/
    └── TreeService_wan_YYYYMMDD_HHMMSS.mp4
```

## API Reference

### VideoGeneratorAgent

```python
class VideoGeneratorAgent:
    def generate_video(specifications: Dict = None) -> str
    def process_video_assets(assets: List[str]) -> Dict
    def list_available_models() -> List[str]
    def get_model_info(model_name: str) -> Dict
```

### WanVideoGenerator

```python
class WanVideoGenerator:
    def generate_video() -> str
    def build_workflow() -> StateGraph
    def enhance_prompt(state: WanVideoState) -> WanVideoState
```

## Dependencies

- `langgraph` - Workflow orchestration
- `langchain` - Framework foundation
- `moviepy` - Video processing
- `matplotlib` - 2D graphics fallback
- `pillow` - Image handling
- `replicate` - AI video generation
- `SpeechRecognition` - Speech-to-text
- `python-dotenv` - Environment configuration
