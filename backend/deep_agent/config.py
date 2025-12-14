# Configuration for deep agent system
from typing import Dict, Any

class DeepAgentConfig:
    """Configuration settings for the deep agent system"""
    
    def __init__(self):
        self.agent_settings = {}
        self.workflow_config = {}
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or environment"""
        return {
            "supervisor": {
                "max_retries": 3,
                "timeout": 300
            },
            "subagents": {
                "ocr_extractor": {"enabled": True},
                "data_analyst": {"enabled": True},
                "video_generator": {"enabled": True}
            }
        }