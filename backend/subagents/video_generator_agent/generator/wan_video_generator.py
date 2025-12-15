#!/usr/bin/env python3
"""
Wan 2.5 Video Generator using Speech-to-Text + Replicate
Converts audio to text, then generates video using Wan 2.5 model
Enhanced with retry logic, better prompts, and improved error handling
"""

import os
import sys
import time
import random
from typing import Dict, List, TypedDict, Optional
from pathlib import Path
import speech_recognition as sr
import replicate
import moviepy as mp
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

from langgraph.graph import StateGraph, END

# Load environment variables from .env file
# Try multiple locations for the .env file
_base_dir = Path(__file__).parent.parent
load_dotenv(_base_dir / ".env")  # Load from video_generator_agent directory
load_dotenv()  # Also try current directory

# Wan 2.5 API Configuration
WAN_CONFIG = {
    "model": "wan-video/wan-2.5-t2v",  # Primary model
    "fallback_models": [
        "minimax/video-01",  # Fallback option 1
        "luma/ray",  # Fallback option 2
    ],
    "max_retries": 3,
    "base_delay": 2,  # Base delay for exponential backoff (seconds)
    "max_delay": 30,  # Maximum delay between retries
    "timeout": 300,  # 5 minute timeout per segment
    "valid_durations": [5, 10],  # Wan 2.5 only supports 5 or 10 second clips
}

class WanVideoState(TypedDict):
    """State for Wan video generation workflow"""
    audio_path: str
    audio_duration: float
    brief_content: Dict
    transcribed_text: str
    enhanced_prompt: str
    video_segments: List[str]
    final_video_path: str
    status: str
    error: str


class WanAPIClient:
    """Enhanced Wan 2.5 API client with retry logic and fallback support"""
    
    def __init__(self):
        self.config = WAN_CONFIG
        self.current_model = self.config["model"]
        self.api_available = bool(os.getenv("REPLICATE_API_TOKEN"))
        
    def generate_video_with_retry(self, prompt: str, duration: int = 5, 
                                   negative_prompt: str = None) -> Optional[bytes]:
        """
        Generate video using Wan 2.5 with retry logic and exponential backoff
        
        Args:
            prompt: The text prompt for video generation
            duration: Video duration (5 or 10 seconds)
            negative_prompt: Things to avoid in the video
            
        Returns:
            Video bytes if successful, None otherwise
        """
        if not self.api_available:
            print("⚠️ REPLICATE_API_TOKEN not set - skipping API call")
            return None
            
        # Validate duration
        if duration not in self.config["valid_durations"]:
            duration = 5 if duration < 7.5 else 10
            
        # Build optimized input for 2D animation
        input_data = self._build_optimized_input(prompt, duration, negative_prompt)
        
        # Try primary model with retries
        result = self._try_model_with_retries(self.current_model, input_data)
        if result:
            return result
            
        # Try fallback models
        for fallback_model in self.config["fallback_models"]:
            print(f"🔄 Trying fallback model: {fallback_model}")
            result = self._try_model_with_retries(fallback_model, input_data)
            if result:
                self.current_model = fallback_model  # Remember working model
                return result
                
        return None
    
    def _build_optimized_input(self, prompt: str, duration: int, 
                                negative_prompt: str = None) -> Dict:
        """Build optimized input parameters for 2D animation generation"""
        
        # Enhance prompt for better 2D animation results
        enhanced_prompt = self._enhance_prompt_for_2d(prompt)
        
        # Default negative prompt for 2D animation
        default_negative = (
            "photorealistic, 3D render, CGI, realistic textures, "
            "live action, real people, photographs, blurry, low quality, "
            "distorted, deformed, ugly, bad anatomy, watermark, text overlay"
        )
        
        input_data = {
            "prompt": enhanced_prompt,
            "duration": duration,
        }
        
        # Add negative prompt if supported
        if negative_prompt:
            input_data["negative_prompt"] = f"{default_negative}, {negative_prompt}"
        else:
            input_data["negative_prompt"] = default_negative
            
        return input_data
    
    def _enhance_prompt_for_2d(self, prompt: str) -> str:
        """Enhance prompt specifically for 2D animation style"""
        
        # Key 2D animation style keywords
        style_prefix = (
            "2D animated explainer video, flat design style, "
            "clean vector graphics, motion graphics, "
            "professional corporate animation, "
        )
        
        style_suffix = (
            " Smooth animations, modern flat design aesthetic, "
            "vibrant colors, clean lines, minimalist style, "
            "professional business animation quality."
        )
        
        # Don't double-add if already present
        if "2D animated" not in prompt:
            prompt = style_prefix + prompt
        if "flat design" not in prompt.lower():
            prompt = prompt + style_suffix
            
        # Limit prompt length (some models have limits)
        words = prompt.split()
        if len(words) > 150:
            prompt = " ".join(words[:150])
            
        return prompt
    
    def _try_model_with_retries(self, model: str, input_data: Dict) -> Optional[bytes]:
        """Try a specific model with exponential backoff retries"""
        
        for attempt in range(self.config["max_retries"]):
            try:
                print(f"🎬 Attempt {attempt + 1}/{self.config['max_retries']} with {model}...")
                
                output = replicate.run(model, input=input_data)
                
                # Handle different output types
                if hasattr(output, 'read'):
                    return output.read()
                elif isinstance(output, str):
                    # URL returned - download it
                    import urllib.request
                    with urllib.request.urlopen(output) as response:
                        return response.read()
                elif isinstance(output, list) and len(output) > 0:
                    # List of URLs
                    import urllib.request
                    with urllib.request.urlopen(output[0]) as response:
                        return response.read()
                else:
                    print(f"⚠️ Unexpected output type: {type(output)}")
                    return None
                    
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Attempt {attempt + 1} failed: {error_msg}")
                
                # Check if it's a retryable error
                if self._is_retryable_error(error_msg):
                    if attempt < self.config["max_retries"] - 1:
                        delay = self._calculate_backoff_delay(attempt)
                        print(f"⏳ Waiting {delay:.1f}s before retry...")
                        time.sleep(delay)
                else:
                    # Non-retryable error, break immediately
                    print(f"🚫 Non-retryable error, skipping remaining attempts")
                    break
                    
        return None
    
    def _is_retryable_error(self, error_msg: str) -> bool:
        """Determine if an error is retryable"""
        
        retryable_patterns = [
            "temporarily unavailable",
            "rate limit",
            "timeout",
            "503",
            "502",
            "504",
            "connection",
            "E004",  # Replicate service unavailable
        ]
        
        error_lower = error_msg.lower()
        return any(pattern.lower() in error_lower for pattern in retryable_patterns)
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter"""
        
        base_delay = self.config["base_delay"]
        max_delay = self.config["max_delay"]
        
        # Exponential backoff: 2^attempt * base_delay
        delay = min(base_delay * (2 ** attempt), max_delay)
        
        # Add random jitter (±25%)
        jitter = delay * 0.25 * (random.random() * 2 - 1)
        
        return delay + jitter

class WanVideoGenerator:
    def __init__(self):
        """Initialize Wan Video Generator"""
        # Use path relative to this file's location
        self.base_dir = Path(__file__).parent.parent
        self.audio_path = str(self.base_dir / "project" / "inputs" / "VoiceOver.wav")
        
        # Create wan-specific output directory
        self.base_output_dir = self.base_dir / "human_deliverable"
        self.base_output_dir.mkdir(exist_ok=True)
        
        self.model_output_dir = self.base_output_dir / "wan-2.5"
        self.model_output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_path = self.model_output_dir / f"TreeService_wan_{timestamp}.mp4"
        
        self.temp_dir = self.base_dir / "temp_wan_videos"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        
        # Initialize Wan API client with retry logic
        self.wan_client = WanAPIClient()
        
        # Track generation statistics
        self.stats = {
            "api_successes": 0,
            "api_failures": 0,
            "fallback_used": 0,
        }
        
        # Build the workflow
        self.workflow = self.build_workflow()
    
    def build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for Wan video generation"""
        
        workflow = StateGraph(WanVideoState)
        
        # Add nodes
        workflow.add_node("load_project_brief", self.load_project_brief)
        workflow.add_node("analyze_audio", self.analyze_audio)
        workflow.add_node("transcribe_speech", self.transcribe_speech)
        workflow.add_node("enhance_prompt", self.enhance_prompt)
        workflow.add_node("generate_video_segments", self.generate_video_segments)
        workflow.add_node("compose_final_video", self.compose_final_video)
        workflow.add_node("cleanup", self.cleanup)
        
        # Define the flow - skip brief loading, start with audio
        workflow.set_entry_point("analyze_audio")
        workflow.add_edge("analyze_audio", "transcribe_speech")
        workflow.add_edge("transcribe_speech", "enhance_prompt")
        workflow.add_edge("enhance_prompt", "generate_video_segments")
        workflow.add_edge("generate_video_segments", "compose_final_video")
        workflow.add_edge("compose_final_video", "cleanup")
        workflow.add_edge("cleanup", END)
        
        return workflow.compile()
    
    def load_project_brief(self, state: WanVideoState) -> WanVideoState:
        """Skip brief loading - use audio only"""
        
        print("🎤 Using audio-only mode (no brief.md)")
        
        # Set minimal default content for video generation
        state["brief_content"] = {
            "work_description": "Tree service company",
            "audience": ["Homeowners"],
            "tone": "Professional",
            "length": "60 seconds",
            "visual_preferences": "Natural colors",
            "video_style": "Professional",
            "script": "",
            "services": []
        }
        state["status"] = "Audio-only mode"
        
        return state
    
    def analyze_audio(self, state: WanVideoState) -> WanVideoState:
        """Analyze audio file to get duration"""
        try:
            audio = mp.AudioFileClip(self.audio_path)
            duration = audio.duration
            audio.close()
            
            state["audio_duration"] = duration
            state["audio_path"] = self.audio_path
            state["status"] = f"Audio analyzed: {duration:.2f}s"
            print(f"🎵 Audio duration: {duration:.2f} seconds")
            
        except Exception as e:
            state["error"] = f"Audio analysis failed: {str(e)}"
            state["status"] = "Error"
            
        return state
    
    def transcribe_speech(self, state: WanVideoState) -> WanVideoState:
        """Convert speech to text using SpeechRecognition"""
        
        try:
            print("🎤 Transcribing speech to text...")
            
            # Load audio file
            with sr.AudioFile(state["audio_path"]) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Record the audio
                audio_data = self.recognizer.record(source)
            
            # Try multiple recognition services for best results
            transcribed_text = None
            
            # Try Google Speech Recognition (free)
            try:
                transcribed_text = self.recognizer.recognize_google(audio_data)
                print("✅ Google Speech Recognition successful")
            except sr.UnknownValueError:
                print("⚠️ Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print(f"⚠️ Google Speech Recognition error: {e}")
            
            # Fallback to offline recognition if Google fails
            if not transcribed_text:
                try:
                    transcribed_text = self.recognizer.recognize_sphinx(audio_data)
                    print("✅ Sphinx (offline) recognition successful")
                except sr.UnknownValueError:
                    print("⚠️ Sphinx could not understand audio")
                except sr.RequestError as e:
                    print(f"⚠️ Sphinx error: {e}")
            
            # Final fallback to script from brief if recognition fails
            if not transcribed_text:
                print("⚠️ Speech recognition failed, using script from project brief")
                transcribed_text = self.get_fallback_script(state.get("brief_content"))
            
            state["transcribed_text"] = transcribed_text
            state["status"] = "Speech transcribed successfully"
            
            print(f"📝 Transcribed text: {transcribed_text[:100]}...")
            
        except Exception as e:
            state["error"] = f"Speech transcription failed: {str(e)}"
            # Use fallback script from brief
            state["transcribed_text"] = self.get_fallback_script(state.get("brief_content"))
            state["status"] = "Using script from project brief"
            print(f"❌ Transcription error, using brief script: {e}")
            
        return state
    
    def get_fallback_script(self, brief_content: Dict = None) -> str:
        """Get fallback script if speech recognition fails"""
        
        # Simple fallback script based on common tree service content
        return """
        Professional tree care services including consultation, assessment, pruning, 
        trimming, stump removal, and cleanup. Expert arborists using modern equipment 
        and safety protocols to provide quality tree care solutions.
        """
    
    def enhance_prompt(self, state: WanVideoState) -> WanVideoState:
        """Create 2D animated video prompts based purely on transcribed audio content"""
        
        try:
            print("✨ Creating 2D animated video prompts from transcribed audio content...")
            
            text = state["transcribed_text"].lower()
            
            # Extract company name from transcribed text
            company_name = "Skyline Tree Services" if "skyline tree services" in text else "Tree Service Company"
            
            # Start with 2D animated video description
            enhanced_prompt = f"2D animated explainer video for {company_name}. "
            enhanced_prompt += "Flat design style, clean vector graphics, modern 2D animation. "
            
            # Add specific 2D animated content based on what's actually spoken in the audio
            if "welcome" in text or "trusted partner" in text:
                enhanced_prompt += "2D animated company logo introduction with text overlay and smooth transitions. "
                enhanced_prompt += "Flat design welcome screen with animated company branding elements. "
            
            if "consultation" in text or "understand" in text or "needs" in text:
                enhanced_prompt += "2D animated scene showing consultation meeting with simple character illustrations. "
                enhanced_prompt += "Flat design icons representing discussion, clipboard, and customer interaction. "
            
            if "assessment" in text or "health" in text or "structure" in text:
                enhanced_prompt += "2D animated tree health evaluation with animated diagnostic icons and charts. "
                enhanced_prompt += "Simple vector illustrations of tree inspection process with motion graphics. "
            
            if "pruning" in text or "trimming" in text or "shaping" in text:
                enhanced_prompt += "2D animated pruning operations with simple tool icons and tree transformation. "
                enhanced_prompt += "Clean vector graphics showing before/after tree shaping with smooth animations. "
            
            if "stump" in text or "removal" in text or "grinding" in text:
                enhanced_prompt += "2D animated stump removal process with simple machinery icons and progress indicators. "
                enhanced_prompt += "Flat design illustration of stump grinding with animated particles and effects. "
            
            if "plan" in text or "customized" in text or "tailored" in text:
                enhanced_prompt += "2D animated planning scene with document icons, charts, and workflow diagrams. "
                enhanced_prompt += "Simple vector graphics showing customized care plan creation with animated elements. "
            
            if "technology" in text or "techniques" in text or "equipment" in text:
                enhanced_prompt += "2D animated modern equipment showcase with clean tech icons and innovation graphics. "
                enhanced_prompt += "Flat design technology illustrations with animated gear icons and progress bars. "
            
            if "safety" in text or "precautions" in text or "protect" in text:
                enhanced_prompt += "2D animated safety protocols with protective equipment icons and warning symbols. "
                enhanced_prompt += "Simple vector illustrations of safety measures with animated checkmarks and shields. "
            
            if "cleanup" in text or "clean" in text or "beautiful" in text:
                enhanced_prompt += "2D animated cleanup process with before/after comparisons and satisfaction icons. "
                enhanced_prompt += "Clean vector graphics showing transformation with animated sparkles and completion badges. "
            
            if "contact" in text or "help" in text:
                enhanced_prompt += "2D animated call-to-action with contact information and animated phone/email icons. "
                enhanced_prompt += "Flat design contact screen with company logo and animated interaction elements. "
            
            # Add 2D animation styling requirements
            enhanced_prompt += """
            2D animated explainer video style with flat design aesthetics, clean vector graphics, 
            smooth motion graphics, natural color palette (greens, browns, light blues), 
            modern typography, simple character illustrations, icon-based animations, 
            subtle transitions, professional 2D animation quality, corporate branding elements.
            No photorealistic elements, no 3D rendering, pure 2D flat design animation.
            """
            
            # Clean up the prompt
            enhanced_prompt = " ".join(enhanced_prompt.split())
            
            state["enhanced_prompt"] = enhanced_prompt
            state["status"] = "2D animated prompt created from audio transcription"
            
            print(f"🎨 2D animated prompt: {enhanced_prompt[:200]}...")
            
        except Exception as e:
            state["error"] = f"Prompt enhancement failed: {str(e)}"
            # Use 2D animated fallback prompt
            state["enhanced_prompt"] = "2D animated explainer video for tree service company, flat design style, clean vector graphics, modern 2D animation"
            print(f"❌ Using 2D animated fallback prompt: {e}")
            
        return state

    def create_detailed_prompt_structure(self, base_prompt: str, segment_details: str) -> str:
        """Create a well-structured, detailed 2D animated video prompt for optimal generation"""
        
        # More concise prompt structure optimized for Wan 2.5
        # Wan 2.5 works better with shorter, more focused prompts
        structured_prompt = f"""
        2D animated explainer video, flat design style, motion graphics.
        
        Scene: {segment_details[:200]}
        
        Style: Clean vector graphics, smooth animations, professional corporate look.
        Colors: Natural greens, browns, light blues, white backgrounds.
        Animation: Subtle movements, icon animations, text overlays, transitions.
        Quality: High-quality 2D animation, modern flat design aesthetic.
        """
        
        return " ".join(structured_prompt.split())  # Clean up whitespace
    
    def validate_and_optimize_prompt(self, prompt: str) -> str:
        """Validate and optimize the prompt for best 2D animated video generation results"""
        
        optimized_prompt = prompt
        
        # Remove any problematic terms that might confuse the model
        problematic_terms = ["photorealistic", "3D render", "CGI", "realistic", "photograph"]
        for term in problematic_terms:
            optimized_prompt = optimized_prompt.replace(term, "2D animated")
        
        # Ensure 2D animation style is at the start (most important for model attention)
        if not optimized_prompt.lower().startswith("2d"):
            optimized_prompt = f"2D animated flat design video: {optimized_prompt}"
        
        # Optimal prompt length for Wan 2.5 is around 50-100 words
        # Too long prompts can confuse the model
        words = optimized_prompt.split()
        if len(words) > 100:
            # Keep the most important parts (beginning and style descriptors)
            optimized_prompt = " ".join(words[:100])
        elif len(words) < 20:
            # Expand if too short
            optimized_prompt += " smooth motion graphics, professional animation, clean design"
        
        # Add quality boosters at the end
        quality_suffix = ", high quality, smooth animation, professional"
        if "high quality" not in optimized_prompt.lower():
            optimized_prompt += quality_suffix
        
        return optimized_prompt
    
    def generate_video_segments(self, state: WanVideoState) -> WanVideoState:
        """Generate video segments using Wan 2.5 model with precise audio synchronization"""
        
        try:
            print("🎬 Generating video with Wan 2.5 model...")
            print(f"🔧 API Available: {self.wan_client.api_available}")
            print(f"🎯 Using model: {self.wan_client.current_model}")
            
            # Check for Replicate API token - if not available, use direct content generation
            if not self.wan_client.api_available:
                print("⚠️ REPLICATE_API_TOKEN not found - using direct content generation")
                return self.generate_direct_content_segments(state)
            
            duration = state["audio_duration"]
            prompt = state["enhanced_prompt"]
            transcribed_text = state["transcribed_text"]
            
            # Analyze transcribed text to create content-aware segments
            audio_segments = self.analyze_audio_content_segments(transcribed_text, duration)
            
            print(f"📹 Generating {len(audio_segments)} content-aware video segments")
            print(f"🎤 Total audio duration: {duration:.2f} seconds")
            print(f"🔄 Max retries per segment: {WAN_CONFIG['max_retries']}")
            
            video_segments = []
            
            for i, segment_info in enumerate(audio_segments):
                start_time = segment_info["start_time"]
                end_time = segment_info["end_time"]
                segment_duration = end_time - start_time
                content_type = segment_info["content_type"]
                content_text = segment_info["text"]
                
                print(f"\n{'='*60}")
                print(f"🎬 Generating segment {i+1}/{len(audio_segments)}...")
                print(f"⏱️  Time: {start_time:.1f}s - {end_time:.1f}s ({segment_duration:.1f}s)")
                print(f"📝 Content: {content_type}")
                print(f"🎤 Audio text: {content_text[:50]}...")
                
                # Create segment-specific prompt based on actual audio content
                segment_prompt = self.create_content_specific_prompt(
                    prompt, content_type, content_text, i, len(audio_segments), state["brief_content"]
                )
                
                # Create structured, detailed prompt for optimal generation
                structured_prompt = self.create_detailed_prompt_structure(prompt, segment_prompt)
                final_prompt = self.validate_and_optimize_prompt(structured_prompt)
                
                print(f"📝 Final prompt length: {len(final_prompt.split())} words")
                print(f"🎯 Prompt preview: {final_prompt[:120]}...")
                
                # Determine Wan duration (5 or 10 seconds only)
                wan_duration = 10 if segment_duration > 7.5 else 5
                
                # Create content-specific negative prompt
                negative_prompt = self._get_negative_prompt_for_content(content_type)
                
                # Use the enhanced API client with retry logic
                video_bytes = self.wan_client.generate_video_with_retry(
                    prompt=final_prompt,
                    duration=wan_duration,
                    negative_prompt=negative_prompt
                )
                
                if video_bytes:
                    # Save video segment with timing info
                    segment_path = self.temp_dir / f"segment_{i+1:02d}_{start_time:.1f}s-{end_time:.1f}s.mp4"
                    
                    with open(segment_path, "wb") as file:
                        file.write(video_bytes)
                    
                    video_segments.append(str(segment_path))
                    self.stats["api_successes"] += 1
                    print(f"✅ Segment {i+1} generated successfully via API!")
                else:
                    print(f"⚠️ API generation failed for segment {i+1}, using fallback...")
                    self.stats["api_failures"] += 1
                    
                    # Create a fallback segment with exact timing and actual content
                    fallback_path = self.create_fallback_segment(i+1, segment_duration, content_type, content_text)
                    if fallback_path:
                        video_segments.append(fallback_path)
                        self.stats["fallback_used"] += 1
                        print(f"✅ Fallback segment {i+1} created")
            
            # Print generation statistics
            print(f"\n{'='*60}")
            print(f"📊 Generation Statistics:")
            print(f"   ✅ API Successes: {self.stats['api_successes']}")
            print(f"   ❌ API Failures: {self.stats['api_failures']}")
            print(f"   🔄 Fallbacks Used: {self.stats['fallback_used']}")
            
            state["video_segments"] = video_segments
            state["status"] = f"Generated {len(video_segments)} content-synchronized video segments"
            
        except Exception as e:
            state["error"] = f"Video generation failed: {str(e)}"
            print(f"❌ Video generation error: {e}")
            import traceback
            traceback.print_exc()
            
        return state
    
    def _get_negative_prompt_for_content(self, content_type: str) -> str:
        """Get content-specific negative prompts to avoid unwanted elements"""
        
        base_negative = "blurry, low quality, distorted, ugly, watermark"
        
        content_negatives = {
            "introduction": f"{base_negative}, cluttered, busy background",
            "consultation": f"{base_negative}, empty room, no people",
            "assessment": f"{base_negative}, dead trees, destruction",
            "pruning": f"{base_negative}, dangerous, accidents",
            "stump_removal": f"{base_negative}, messy, incomplete",
            "planning": f"{base_negative}, disorganized, chaotic",
            "technology": f"{base_negative}, outdated, broken equipment",
            "safety": f"{base_negative}, unsafe, accidents, injuries",
            "cleanup": f"{base_negative}, dirty, messy, incomplete",
            "call_to_action": f"{base_negative}, unclear, hard to read",
        }
        
        return content_negatives.get(content_type, base_negative)
    
    def analyze_audio_content_segments(self, transcribed_text: str, total_duration: float) -> List[Dict]:
        """Analyze transcribed text to create content-aware segments that match audio timing"""
        
        # Wan 2.5 only supports 5 or 10 second segments, so we need to plan accordingly
        max_segment_duration = 10
        min_segment_duration = 5
        
        # Calculate optimal number of segments
        num_segments = max(1, int(total_duration / max_segment_duration))
        if total_duration / num_segments < min_segment_duration:
            num_segments = max(1, int(total_duration / min_segment_duration))
        
        segment_duration = total_duration / num_segments
        
        # Split text into logical segments based on content
        sentences = [s.strip() for s in transcribed_text.split('.') if s.strip()]
        
        if not sentences or len(sentences) < num_segments:
            # Use time-based segments with content classification
            segments = []
            for i in range(num_segments):
                start_time = i * segment_duration
                end_time = min((i + 1) * segment_duration, total_duration)
                
                # Get text portion for this time segment
                text_portion = self.get_text_for_time_segment(transcribed_text, i, num_segments)
                content_type = self.classify_sentence_content(text_portion)
                
                segments.append({
                    "start_time": start_time,
                    "end_time": end_time,
                    "content_type": content_type,
                    "text": text_portion
                })
            
            return segments
        
        # Create segments based on sentence content and estimated timing
        segments = []
        sentences_per_segment = max(1, len(sentences) // num_segments)
        
        for i in range(num_segments):
            start_sentence_idx = i * sentences_per_segment
            end_sentence_idx = min((i + 1) * sentences_per_segment, len(sentences))
            
            # Combine sentences for this segment
            segment_sentences = sentences[start_sentence_idx:end_sentence_idx]
            segment_text = '. '.join(segment_sentences)
            
            # Calculate timing
            start_time = i * segment_duration
            end_time = min((i + 1) * segment_duration, total_duration)
            
            # Determine content type based on combined text
            content_type = self.classify_sentence_content(segment_text)
            
            segments.append({
                "start_time": start_time,
                "end_time": end_time,
                "content_type": content_type,
                "text": segment_text
            })
        
        # Adjust final segment to match total duration exactly
        if segments and segments[-1]["end_time"] < total_duration:
            segments[-1]["end_time"] = total_duration
        
        return segments
    
    def generate_direct_content_segments(self, state: WanVideoState) -> WanVideoState:
        """Generate video segments directly from transcribed content without Wan 2.5 API"""
        
        try:
            print("🎬 Generating video segments directly from transcribed content...")
            
            duration = state["audio_duration"]
            transcribed_text = state["transcribed_text"]
            
            # Analyze transcribed text to create content-aware segments
            audio_segments = self.analyze_audio_content_segments(transcribed_text, duration)
            
            print(f"📹 Creating {len(audio_segments)} content-rich video segments")
            print(f"🎤 Total audio duration: {duration:.2f} seconds")
            
            video_segments = []
            
            for i, segment_info in enumerate(audio_segments):
                start_time = segment_info["start_time"]
                end_time = segment_info["end_time"]
                segment_duration = end_time - start_time
                content_type = segment_info["content_type"]
                content_text = segment_info["text"]
                
                print(f"\n🎬 Creating segment {i+1}/{len(audio_segments)}...")
                print(f"⏱️  Time: {start_time:.1f}s - {end_time:.1f}s ({segment_duration:.1f}s)")
                print(f"📝 Content: {content_type}")
                print(f"🎤 Audio text: {content_text[:50]}...")
                
                # Create rich content segment directly
                segment_path = self.create_fallback_segment(i+1, segment_duration, content_type, content_text)
                
                if segment_path:
                    video_segments.append(segment_path)
                    print(f"✅ Segment {i+1} created: {segment_path}")
                else:
                    print(f"❌ Failed to create segment {i+1}")
            
            state["video_segments"] = video_segments
            state["status"] = f"Generated {len(video_segments)} content-rich video segments"
            
        except Exception as e:
            state["error"] = f"Direct content generation failed: {str(e)}"
            print(f"❌ Direct content generation error: {e}")
            
        return state
    
    def get_text_for_time_segment(self, full_text: str, segment_index: int, total_segments: int) -> str:
        """Get the portion of text that corresponds to a specific time segment"""
        
        words = full_text.split()
        words_per_segment = len(words) // total_segments
        
        start_word = segment_index * words_per_segment
        end_word = min((segment_index + 1) * words_per_segment, len(words))
        
        if segment_index == total_segments - 1:  # Last segment gets remaining words
            end_word = len(words)
        
        return ' '.join(words[start_word:end_word])
    
    def classify_sentence_content(self, sentence: str) -> str:
        """Classify sentence content to determine appropriate visual style"""
        
        sentence_lower = sentence.lower()
        
        if any(word in sentence_lower for word in ["welcome", "skyline tree services", "trusted partner"]):
            return "introduction"
        elif any(word in sentence_lower for word in ["consultation", "understand", "needs"]):
            return "consultation"
        elif any(word in sentence_lower for word in ["assessment", "health", "structure", "evaluate"]):
            return "assessment"
        elif any(word in sentence_lower for word in ["pruning", "trimming", "shaping", "cutting"]):
            return "pruning"
        elif any(word in sentence_lower for word in ["stump", "removal", "grinding"]):
            return "stump_removal"
        elif any(word in sentence_lower for word in ["plan", "customized", "tailored", "requirements"]):
            return "planning"
        elif any(word in sentence_lower for word in ["technology", "techniques", "equipment", "tools"]):
            return "technology"
        elif any(word in sentence_lower for word in ["safety", "precautions", "protect"]):
            return "safety"
        elif any(word in sentence_lower for word in ["cleanup", "clean", "beautiful", "finished"]):
            return "cleanup"
        elif any(word in sentence_lower for word in ["contact", "help", "call"]):
            return "call_to_action"
        else:
            return "general"

    def create_content_specific_prompt(self, base_prompt: str, content_type: str, content_text: str, 
                                     segment_index: int, total_segments: int, brief_content: Dict) -> str:
        """Create 2D animated content-specific prompts based on actual audio content"""
        
        # Extract company name from the actual transcribed text
        company_name = "Skyline Tree Services" if "skyline tree services" in content_text.lower() else "Tree Service Company"
        
        content_prompts = {
            "introduction": f"""
            2D ANIMATED INTRODUCTION SCENE: Flat design welcome and company introduction for {company_name}.
            AUDIO CONTENT: "{content_text}"
            2D VISUAL ELEMENTS: Large animated {company_name} logo with smooth transitions, clean typography, 
            professional branding elements, welcoming color scheme (greens, blues).
            2D SCENE COMPOSITION: Clean corporate introduction with animated text overlays, 
            simple vector graphics, flat design aesthetic.
            ANIMATION STYLE: Modern 2D motion graphics, flat design, no photorealistic elements.
            """,
            
            "consultation": f"""
            2D ANIMATED CONSULTATION SCENE: Flat design arborist consultation meeting.
            AUDIO CONTENT: "{content_text}"
            2D VISUAL ELEMENTS: Simple character illustrations in consultation, animated clipboard icons, 
            assessment form graphics, pointing gestures with motion graphics.
            2D SCENE COMPOSITION: Clean vector illustration of professional interaction, 
            flat design characters, animated dialogue bubbles.
            ANIMATION STYLE: Simple 2D character animation, icon-based motion graphics.
            """,
            
            "assessment": f"""
            2D ANIMATED ASSESSMENT SCENE: Flat design tree health evaluation and analysis.
            AUDIO CONTENT: "{content_text}"
            2D VISUAL ELEMENTS: Animated tree inspection icons, measuring tool graphics, 
            diagnostic chart animations, health indicator symbols.
            2D SCENE COMPOSITION: Vector illustration of tree examination with animated 
            assessment elements, progress bars, checkmark animations.
            ANIMATION STYLE: Clean 2D infographic style, animated data visualization.
            """,
            
            "pruning": f"""
            2D ANIMATED PRUNING SCENE: Flat design tree pruning and trimming operations.
            AUDIO CONTENT: "{content_text}"
            2D VISUAL ELEMENTS: Animated pruning tool icons, tree transformation graphics, 
            before/after comparisons, safety equipment symbols.
            2D SCENE COMPOSITION: Simple vector illustration of pruning process with 
            animated cutting motions, falling branch graphics, tree shaping progression.
            ANIMATION STYLE: Clean 2D process animation, step-by-step visual flow.
            """,
            
            "stump_removal": f"""
            2D ANIMATED STUMP REMOVAL SCENE: Flat design stump removal and grinding operations.
            AUDIO CONTENT: "{content_text}"
            2D VISUAL ELEMENTS: Animated stump grinder icons, removal process graphics, 
            machinery symbols, progress indicators, particle effects.
            2D SCENE COMPOSITION: Vector illustration of stump grinding with animated 
            machinery operation, debris particles, completion indicators.
            ANIMATION STYLE: Industrial 2D animation, mechanical motion graphics.
            """,
            
            "planning": f"""
            2D ANIMATED PLANNING SCENE: Flat design customized tree care plan creation.
            AUDIO CONTENT: "{content_text}"
            2D VISUAL ELEMENTS: Animated document icons, tree diagram graphics, 
            planning workflow charts, consultation material symbols.
            2D SCENE COMPOSITION: Clean vector illustration of planning process with 
            animated document creation, flowchart progression, checkmark completions.
            ANIMATION STYLE: Professional 2D workflow animation, document motion graphics.
            """,
            
            "technology": f"""
            2D ANIMATED TECHNOLOGY SCENE: Flat design modern tree care technology showcase.
            AUDIO CONTENT: "{content_text}"
            2D VISUAL ELEMENTS: Animated equipment icons, innovative tool graphics, 
            technology symbols, gear animations, progress indicators.
            2D SCENE COMPOSITION: Vector illustration of advanced technology with 
            animated tech elements, rotating gears, innovation symbols.
            ANIMATION STYLE: Modern 2D tech animation, futuristic flat design elements.
            """,
            
            "safety": f"""
            2D ANIMATED SAFETY SCENE: Flat design safety protocols and protective equipment.
            AUDIO CONTENT: "{content_text}"
            2D VISUAL ELEMENTS: Animated safety equipment icons, protective gear graphics, 
            warning symbols, safety protocol checklists, shield animations.
            2D SCENE COMPOSITION: Vector illustration of safety measures with animated 
            protective equipment, safety checkmarks, warning indicators.
            ANIMATION STYLE: Safety-focused 2D animation, protective symbol motion graphics.
            """,
            
            "cleanup": f"""
            2D ANIMATED CLEANUP SCENE: Flat design cleanup process and beautiful results.
            AUDIO CONTENT: "{content_text}"
            2D VISUAL ELEMENTS: Animated cleanup icons, before/after comparison graphics, 
            debris removal symbols, satisfaction badges, sparkle effects.
            2D SCENE COMPOSITION: Vector illustration of cleanup transformation with 
            animated cleaning process, completion celebrations, result showcases.
            ANIMATION STYLE: Satisfying 2D transformation animation, completion motion graphics.
            """,
            
            "call_to_action": f"""
            2D ANIMATED CALL TO ACTION SCENE: Flat design conclusion with contact information.
            AUDIO CONTENT: "{content_text}"
            2D VISUAL ELEMENTS: Animated {company_name} logo, contact information graphics, 
            phone/email icons, interaction buttons, call-to-action elements.
            2D SCENE COMPOSITION: Clean vector contact screen with animated logo, 
            contact details, encouraging interaction elements.
            ANIMATION STYLE: Professional 2D call-to-action animation, contact motion graphics.
            """,
            
            "general": f"""
            2D ANIMATED PROFESSIONAL SERVICE SCENE: Flat design {company_name} expert tree care demonstration.
            AUDIO CONTENT: "{content_text}"
            2D VISUAL ELEMENTS: Simple character illustrations of professional arborists, 
            animated equipment icons, quality service symbols, expert delivery graphics.
            2D SCENE COMPOSITION: Clean vector illustration of high-quality workmanship, 
            professional tree care service with animated elements.
            ANIMATION STYLE: Expert 2D service animation, reliable motion graphics, professional flat design.
            """
        }
        
        return content_prompts.get(content_type, content_prompts["general"])
    
    def create_fallback_segment(self, segment_num: int, duration: float, content_type: str = "general", 
                              content_text: str = "") -> str:
        """Create a sophisticated fallback video segment using actual transcribed content"""
        
        print(f"🎨 Creating content-rich fallback segment {segment_num} ({content_type})...")
        
        # Use simple text segment directly since langgraph_video_generator may not be available
        return self.create_simple_text_segment(segment_num, duration, content_type, content_text)
    
    def create_scene_from_transcription(self, content_type: str, content_text: str, segment_num: int) -> Dict:
        """Create scene data based on transcribed audio content"""
        
        # Extract company name from transcribed text
        company_name = "Skyline Tree Services" if "skyline tree services" in content_text.lower() else "Tree Service Company"
        
        scene_templates = {
            "introduction": {
                "title": f"Welcome to {company_name}",
                "subtitle": "Professional Tree Care Services",
                "background_color": "#2E7D32",  # Dark green
                "text_color": "white",
                "icons": ["🌳", "🏠", "⭐"],
                "description": "Professional tree care services you can trust"
            },
            "consultation": {
                "title": "Professional Consultation", 
                "subtitle": "Understanding Your Tree Care Needs",
                "background_color": "#1565C0",  # Dark blue
                "text_color": "white", 
                "icons": ["👥", "📋", "🌳"],
                "description": "Expert assessment of your specific requirements"
            },
            "assessment": {
                "title": "Tree Health Assessment",
                "subtitle": "Detailed Evaluation & Structure Analysis", 
                "background_color": "#E65100",  # Dark orange
                "text_color": "white",
                "icons": ["🔍", "🌳", "📊"],
                "description": "Comprehensive tree health and safety evaluation"
            },
            "pruning": {
                "title": "Expert Pruning & Trimming",
                "subtitle": "Professional Tree Shaping Services",
                "background_color": "#2E7D32",  # Dark green
                "text_color": "white",
                "icons": ["✂️", "🌳", "🛠️"],
                "description": "Skilled pruning for healthy, beautiful trees"
            },
            "stump_removal": {
                "title": "Stump Removal & Grinding", 
                "subtitle": "Complete Stump Elimination",
                "background_color": "#5D4037",  # Brown
                "text_color": "white",
                "icons": ["🪓", "⚙️", "🌳"],
                "description": "Professional stump grinding and removal"
            },
            "planning": {
                "title": "Customized Care Plans",
                "subtitle": "Tailored Tree Care Solutions",
                "background_color": "#7B1FA2",  # Purple  
                "text_color": "white",
                "icons": ["📋", "🎯", "🌳"],
                "description": "Personalized plans for each tree's needs"
            },
            "technology": {
                "title": "Modern Technology & Techniques",
                "subtitle": "Latest Equipment & Methods",
                "background_color": "#37474F",  # Dark gray
                "text_color": "white", 
                "icons": ["🔧", "⚙️", "🚀"],
                "description": "State-of-the-art tools and techniques"
            },
            "safety": {
                "title": "Safety First Priority",
                "subtitle": "Protecting Your Property & Our Team", 
                "background_color": "#C62828",  # Dark red
                "text_color": "white",
                "icons": ["🦺", "⛑️", "🛡️"],
                "description": "Comprehensive safety protocols and protection"
            },
            "cleanup": {
                "title": "Professional Cleanup",
                "subtitle": "Leaving Your Space Beautiful",
                "background_color": "#2E7D32",  # Dark green
                "text_color": "white", 
                "icons": ["🧹", "✨", "🏡"],
                "description": "Thorough cleanup and pristine results"
            },
            "call_to_action": {
                "title": f"Contact {company_name}",
                "subtitle": "Let Us Help You Care for Your Trees",
                "background_color": "#1565C0",  # Dark blue
                "text_color": "white",
                "icons": ["📞", "🌳", "💚"],
                "description": "Get in touch for expert tree care services"
            }
        }
        
        # Get template or use general
        template = scene_templates.get(content_type, {
            "title": "Skyline Tree Services",
            "subtitle": "Professional Tree Care",
            "background_color": "#2E7D32",
            "text_color": "white", 
            "icons": ["🌳", "🏠", "⭐"],
            "description": "Expert tree care services"
        })
        
        # Customize based on actual transcribed content
        if "consultation" in content_text.lower():
            template["subtitle"] = "Understanding Your Specific Needs"
        elif "assessment" in content_text.lower():
            template["subtitle"] = "Professional Tree Evaluation"
        elif "pruning" in content_text.lower() or "trimming" in content_text.lower():
            template["subtitle"] = "Expert Pruning & Shaping"
        elif "safety" in content_text.lower():
            template["subtitle"] = "Safety is Our Top Priority"
        elif "cleanup" in content_text.lower():
            template["subtitle"] = "Beautiful, Clean Results"
        
        return template

    def create_simple_text_segment(self, segment_num: int, duration: float, content_type: str, content_text: str) -> str:
        """Create a simple text-based video segment as final fallback"""
        
        try:
            import matplotlib.pyplot as plt
            
            fig, ax = plt.subplots(figsize=(19.2, 10.8), dpi=100)
            
            # Use clean, professional titles based on content type
            # Don't display raw transcribed text or prompts - use polished titles
            content_info = {
                "introduction": "Welcome to\nSkyline Tree Services\nYour Trusted Partner",
                "consultation": "Professional Consultation\nUnderstanding Your Needs",
                "assessment": "Tree Health Assessment\nExpert Evaluation",
                "pruning": "Expert Pruning\nProfessional Tree Care",
                "stump_removal": "Stump Removal\nComplete Solutions",
                "planning": "Customized Planning\nTailored Solutions",
                "technology": "Modern Technology\nAdvanced Techniques", 
                "safety": "Safety First\nProtecting Everyone",
                "cleanup": "Professional Cleanup\nBeautiful Results",
                "call_to_action": "Contact Us Today\nSkyline Tree Services",
                "general": "Skyline Tree Services\nProfessional Tree Care"
            }
            display_text = content_info.get(content_type, content_info["general"])
            
            # Style based on content type
            colors = {
                "introduction": ("darkgreen", "lightgreen"),
                "consultation": ("darkblue", "lightblue"), 
                "assessment": ("darkorange", "lightyellow"),
                "pruning": ("darkgreen", "lightgreen"),
                "stump_removal": ("saddlebrown", "wheat"),
                "planning": ("darkviolet", "lavender"),
                "technology": ("darkslategray", "lightgray"),
                "safety": ("darkred", "lightcoral"),
                "cleanup": ("darkgreen", "lightgreen"),
                "call_to_action": ("darkblue", "lightblue"),
                "general": ("darkgreen", "lightgreen")
            }
            
            text_color, bg_color = colors.get(content_type, colors["general"])
            
            ax.text(0.5, 0.5, display_text, 
                   ha='center', va='center', fontsize=24, 
                   transform=ax.transAxes, color=text_color, weight='bold',
                   wrap=True)
            ax.set_facecolor(bg_color)
            ax.axis('off')
            
            image_path = self.temp_dir / f"simple_segment_{segment_num}_{content_type}.png"
            plt.savefig(image_path, bbox_inches='tight', facecolor=bg_color)
            plt.close()
            
            # Convert to video
            clip = mp.ImageClip(str(image_path)).with_duration(duration)
            video_path = self.temp_dir / f"simple_segment_{segment_num}_{content_type}.mp4"
            clip.write_videofile(str(video_path), fps=24)
            clip.close()
            
            return str(video_path)
            
        except Exception as e:
            print(f"❌ Simple text segment creation failed: {e}")
            return None
    
    def compose_final_video(self, state: WanVideoState) -> WanVideoState:
        """Compose final video from segments and add original audio"""
        
        try:
            print("🎞️ Composing final video...")
            
            # Load all video segments
            clips = []
            for segment_path in state["video_segments"]:
                if segment_path and os.path.exists(segment_path):
                    clip = mp.VideoFileClip(segment_path)
                    clips.append(clip)
            
            if not clips:
                state["error"] = "No valid video segments to compose"
                return state
            
            # Concatenate all clips
            if len(clips) == 1:
                final_video = clips[0]
            else:
                final_video = mp.concatenate_videoclips(clips)
            
            # Add original audio
            audio = mp.AudioFileClip(state["audio_path"])
            
            # Adjust video duration to match audio
            if final_video.duration != audio.duration:
                if final_video.duration > audio.duration:
                    final_video = final_video.subclipped(0, audio.duration)
                else:
                    # Loop video if it's shorter than audio
                    loops_needed = int(audio.duration / final_video.duration) + 1
                    final_video = mp.concatenate_videoclips([final_video] * loops_needed)
                    final_video = final_video.subclipped(0, audio.duration)
            
            # Combine video and audio
            final_video_with_audio = final_video.with_audio(audio)
            
            # Write final output
            final_video_with_audio.write_videofile(
                str(self.output_path),
                fps=24,
                codec='libx264',
                audio_codec='aac'
            )
            
            # Cleanup
            for clip in clips:
                clip.close()
            final_video.close()
            audio.close()
            final_video_with_audio.close()
            
            state["final_video_path"] = str(self.output_path)
            state["status"] = "Video composition completed"
            
            print(f"✅ Final video saved: {self.output_path}")
            
        except Exception as e:
            state["error"] = f"Video composition failed: {str(e)}"
            print(f"❌ Composition error: {e}")
            
        return state
    
    def cleanup(self, state: WanVideoState) -> WanVideoState:
        """Clean up temporary files"""
        
        try:
            # Remove temporary video segments
            for segment_path in state.get("video_segments", []):
                if segment_path and os.path.exists(segment_path):
                    os.remove(segment_path)
            
            # Remove temporary images
            for temp_file in self.temp_dir.glob("*.png"):
                temp_file.unlink()
            
            # Remove temp directory if empty
            if self.temp_dir.exists() and not any(self.temp_dir.iterdir()):
                self.temp_dir.rmdir()
            
            state["status"] = "Cleanup completed"
            print("🧹 Temporary files cleaned up")
            
        except Exception as e:
            print(f"Cleanup warning: {str(e)}")
            
        return state
    
    def generate_video(self) -> str:
        """Generate the complete video using Wan 2.5 model"""
        
        print("🚀 Starting Wan 2.5 video generation...")
        print("🎤 Speech-to-Text + 🎬 AI Video Generation")
        
        # Initial state
        initial_state = WanVideoState(
            audio_path="",
            audio_duration=0.0,
            brief_content={},
            transcribed_text="",
            enhanced_prompt="",
            video_segments=[],
            final_video_path="",
            status="Starting",
            error=""
        )
        
        # Run the workflow
        result = self.workflow.invoke(initial_state)
        
        if result.get("error"):
            print(f"❌ Error: {result['error']}")
            return None
        
        print(f"🎉 Wan video generation completed: {result['status']}")
        return result.get("final_video_path")


if __name__ == "__main__":
    generator = WanVideoGenerator()
    output_file = generator.generate_video()
    
    if output_file:
        print(f"✅ Wan video generation successful: {output_file}")
    else:
        print("❌ Wan video generation failed")
