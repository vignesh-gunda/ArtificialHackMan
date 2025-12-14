# Video Generator Agent using DeepAgents
from typing import Dict, Any, List, Optional
from pathlib import Path

from .generator import WanVideoGenerator


class VideoGeneratorAgent:
    """Video generation agent using DeepAgents framework"""
    
    def __init__(self):
        self.generation_models = ['wan-2.5']
        self.video_processors = {}
        self._wan_generator = None
    
    @property
    def wan_generator(self) -> WanVideoGenerator:
        """Lazy initialization of Wan video generator"""
        if self._wan_generator is None:
            self._wan_generator = WanVideoGenerator()
        return self._wan_generator
    
    def generate_video(self, specifications: Optional[Dict[str, Any]] = None) -> str:
        """Generate video based on specifications
        
        Args:
            specifications: Optional dict with video generation parameters
                - model: 'wan' (default)
                - audio_path: Path to audio file
                
        Returns:
            Path to generated video file
        """
        model = specifications.get('model', 'wan') if specifications else 'wan'
        
        if model == 'wan':
            return self.wan_generator.generate_video()
        else:
            raise ValueError(f"Unknown model: {model}. Available models: {self.generation_models}")
    
    def process_video_assets(self, assets: List[str]) -> Dict[str, Any]:
        """Process video assets and prepare for generation
        
        Args:
            assets: List of asset file paths
            
        Returns:
            Dict with processed asset information
        """
        processed = {
            'audio_files': [],
            'video_files': [],
            'image_files': [],
            'other_files': []
        }
        
        for asset in assets:
            path = Path(asset)
            suffix = path.suffix.lower()
            
            if suffix in ['.wav', '.mp3', '.aac', '.m4a']:
                processed['audio_files'].append(asset)
            elif suffix in ['.mp4', '.mov', '.avi', '.mkv']:
                processed['video_files'].append(asset)
            elif suffix in ['.png', '.jpg', '.jpeg', '.gif']:
                processed['image_files'].append(asset)
            else:
                processed['other_files'].append(asset)
        
        return processed
    
    def list_available_models(self) -> List[str]:
        """List available video generation models"""
        return self.generation_models.copy()
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dict with model information
        """
        model_info = {
            'wan-2.5': {
                'name': 'Wan 2.5 AI Video Generator',
                'description': '2D animated video generation using Wan 2.5 model',
                'features': [
                    'Speech-to-text transcription',
                    '2D animated flat design style',
                    'Content-aware video segments',
                    'Audio synchronization'
                ],
                'requirements': ['REPLICATE_API_TOKEN (optional)'],
                'output_format': 'MP4 (1080p)',
                'style': '2D animated, flat design, vector graphics'
            }
        }
        
        return model_info.get(model_name, {'error': f'Model {model_name} not found'})