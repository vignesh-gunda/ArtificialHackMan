#!/usr/bin/env python3
"""
Setup script for Video Generator Agent
"""

import sys
import subprocess
from pathlib import Path


def setup_environment():
    """Setup Python environment and dependencies"""
    print("🔧 Setting up Video Generator Agent")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version_info
    print(f"Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Get the directory of this script
    script_dir = Path(__file__).parent
    requirements_file = script_dir / "requirements.txt"
    
    # Install requirements
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False
    
    # Test imports
    print("\n🧪 Testing imports...")
    try:
        from video_generator_agent.generator.wan_video_generator import WanVideoGenerator
        print("✅ WanVideoGenerator loaded successfully")
    except ImportError as e:
        print(f"⚠️ Import test failed (may work from project root): {e}")
    
    try:
        from video_generator_agent.deepagent_subsystem import VideoGeneratorAgent
        print("✅ VideoGeneratorAgent loaded successfully")
    except ImportError as e:
        print(f"⚠️ Import test failed (may work from project root): {e}")
    
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("   python video_generator_agent/generate_video.py        # Generate video")
    print("   python video_generator_agent/generate_video.py --list # List videos")
    
    return True


if __name__ == "__main__":
    success = setup_environment()
    sys.exit(0 if success else 1)
