#!/usr/bin/env python3
"""
Main entry point for Tree Service Video Generation
Interactive model selection with Wan 2.5 AI options
"""

import sys
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def show_model_selection():
    """Show interactive model selection menu"""
    print("🎬 Tree Service Video Generator")
    print("=" * 50)
    
    # Check system capabilities
    has_replicate_token = bool(os.getenv("REPLICATE_API_TOKEN"))
    
    print("Available video generation models:\n")
    
    print("1. 🤖 Wan 2.5 AI Generator")
    print("   • Speech-to-text + AI video generation")
    print("   • 2D animated flat design output")
    print("   • Professional corporate style")
    print("   • Requires Replicate API token (optional)")
    if has_replicate_token:
        print("   ✅ API token detected")
    else:
        print("   ⚠️  API token not found - will use fallback generation")
    
    print("\n2. 📋 List Generated Videos")
    print("   • View all previously generated videos")
    
    print("\n" + "=" * 50)
    
    while True:
        try:
            choice = input("Select option (1-2) or 'q' to quit: ").strip().lower()
            
            if choice == 'q' or choice == 'quit':
                print("👋 Goodbye!")
                sys.exit(0)
            elif choice == '1':
                return 'wan'
            elif choice == '2':
                return 'list'
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 'q'")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Generate Tree Service Videos")
    parser.add_argument(
        "generator", 
        choices=["wan", "interactive"],
        default="interactive",
        nargs="?",
        help="Generator type: wan or interactive (default)"
    )
    parser.add_argument(
        "--list", 
        action="store_true",
        help="List all generated videos"
    )
    
    args = parser.parse_args()
    
    # Handle list command
    if args.list:
        from video_generator_agent.utils.list_outputs import list_generated_videos
        list_generated_videos()
        return
    
    # Determine which generator to use
    if args.generator == "interactive":
        selected_model = show_model_selection()
    else:
        selected_model = args.generator
    
    # Handle list selection from interactive menu
    if selected_model == "list":
        from video_generator_agent.utils.list_outputs import list_generated_videos
        list_generated_videos()
        return
    
    # Generate video based on selected method
    print(f"\n🚀 Starting video generation...")
    
    if selected_model == "wan":
        print("🤖 Using Wan 2.5 AI video generator...")
        print("⏱️  Estimated time: ~15-20 minutes (with API) or ~2 minutes (fallback)")
        print("🎤 Converting speech to text...")
        print("🎬 Generating 2D animated video segments...")
        
        from video_generator_agent.generator.wan_video_generator import WanVideoGenerator
        generator = WanVideoGenerator()
        output_path = generator.generate_video()
    
    # Show results
    if output_path:
        print(f"\n🎉 Video generated successfully!")
        print(f"📁 Location: {output_path}")
        
        # Show file info
        try:
            file_size = Path(output_path).stat().st_size
            size_mb = file_size / (1024 * 1024)
            print(f"📊 File size: {size_mb:.1f} MB")
        except:
            pass
        
        print(f"\n📋 Next steps:")
        print(f"   python video_generator_agent/generate_video.py --list    # List all videos")
        print(f"   python video_generator_agent/generate_video.py           # Generate another video")
        
        # Ask if user wants to generate another video
        try:
            another = input(f"\nGenerate another video? (y/N): ").strip().lower()
            if another == 'y':
                print("\n" + "="*50)
                main()  # Recursive call for another generation
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            
    else:
        print(f"\n❌ Video generation failed")
        
        # Ask if user wants to try again
        try:
            retry = input(f"\nTry again? (y/N): ").strip().lower()
            if retry == 'y':
                print("\n" + "="*50)
                main()  # Recursive call to try again
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
