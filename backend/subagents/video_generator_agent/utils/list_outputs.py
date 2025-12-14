#!/usr/bin/env python3
"""
List all generated videos organized by model
"""

from pathlib import Path
import os
from datetime import datetime

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"

def get_video_info(video_path):
    """Get video file information"""
    try:
        import subprocess
        result = subprocess.run([
            "ffprobe", "-v", "quiet", 
            "-show_entries", "format=duration,size",
            "-show_entries", "stream=width,height",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ], capture_output=True, text=True)
        
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 4:
            width = lines[0]
            height = lines[1] 
            duration = float(lines[2])
            size = int(lines[3])
            
            return {
                'resolution': f"{width}x{height}",
                'duration': f"{duration:.1f}s",
                'size': format_file_size(size)
            }
    except:
        pass
    
    # Fallback to basic file info
    stat = video_path.stat()
    return {
        'resolution': 'Unknown',
        'duration': 'Unknown', 
        'size': format_file_size(stat.st_size)
    }

def list_generated_videos():
    """List all generated videos by model"""
    
    print("🎬 Generated Tree Service Videos")
    print("=" * 60)
    
    deliverable_dir = Path("human_deliverable")
    
    if not deliverable_dir.exists():
        print("❌ No human_deliverable directory found")
        return
    
    # Model directories to check
    model_dirs = {
        "matplotlib": "📊 Matplotlib (LangGraph Graphics)",
        "wan-2.5": "🤖 Wan 2.5 (AI Video Generation)"
    }
    
    total_videos = 0
    
    for model_name, description in model_dirs.items():
        model_dir = deliverable_dir / model_name
        
        if model_dir.exists():
            videos = list(model_dir.glob("*.mp4"))
            
            if videos:
                print(f"\n{description}")
                print("-" * 50)
                
                for video in videos:
                    info = get_video_info(video)
                    modified_time = datetime.fromtimestamp(video.stat().st_mtime)
                    
                    print(f"📄 {video.name}")
                    print(f"   📏 Resolution: {info['resolution']}")
                    print(f"   ⏱️  Duration: {info['duration']}")
                    print(f"   💾 Size: {info['size']}")
                    print(f"   📅 Created: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   📁 Path: {video}")
                    print()
                    
                    total_videos += 1
    
    # Check for any videos in the root deliverable directory
    root_videos = [f for f in deliverable_dir.glob("*.mp4")]
    if root_videos:
        print(f"\n📂 Root Directory Videos")
        print("-" * 50)
        for video in root_videos:
            info = get_video_info(video)
            modified_time = datetime.fromtimestamp(video.stat().st_mtime)
            
            print(f"📄 {video.name}")
            print(f"   📏 Resolution: {info['resolution']}")
            print(f"   ⏱️  Duration: {info['duration']}")
            print(f"   💾 Size: {info['size']}")
            print(f"   📅 Created: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   📁 Path: {video}")
            print()
            
            total_videos += 1
    
    print("=" * 60)
    print(f"📊 Total videos found: {total_videos}")
    
    if total_videos == 0:
        print("\n💡 No videos found. Generate some videos first:")
        print("   • python video_generator_agent/generate_video.py wan")
        print("   • python video_generator_agent/generate_video.py")
    else:
        print(f"\n🎯 Latest video locations:")
        # Find the most recent video
        all_videos = []
        for model_dir in deliverable_dir.iterdir():
            if model_dir.is_dir():
                all_videos.extend(model_dir.glob("*.mp4"))
        all_videos.extend(deliverable_dir.glob("*.mp4"))
        
        if all_videos:
            latest_video = max(all_videos, key=lambda x: x.stat().st_mtime)
            print(f"   📍 Most recent: {latest_video}")

def clean_old_videos():
    """Clean old video files (interactive)"""
    
    deliverable_dir = Path("human_deliverable")
    if not deliverable_dir.exists():
        return
    
    all_videos = []
    for model_dir in deliverable_dir.iterdir():
        if model_dir.is_dir():
            all_videos.extend(model_dir.glob("*.mp4"))
    all_videos.extend(deliverable_dir.glob("*.mp4"))
    
    if not all_videos:
        print("No videos to clean")
        return
    
    print(f"\n🧹 Found {len(all_videos)} video files")
    choice = input("Do you want to delete old videos? (y/N): ").strip().lower()
    
    if choice == 'y':
        deleted_count = 0
        for video in all_videos:
            try:
                video.unlink()
                print(f"   ❌ Deleted: {video}")
                deleted_count += 1
            except Exception as e:
                print(f"   ⚠️  Failed to delete {video}: {e}")
        
        print(f"\n✅ Deleted {deleted_count} video files")
        
        # Remove empty directories
        for model_dir in deliverable_dir.iterdir():
            if model_dir.is_dir() and not any(model_dir.iterdir()):
                try:
                    model_dir.rmdir()
                    print(f"   📁 Removed empty directory: {model_dir}")
                except:
                    pass

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_old_videos()
    else:
        list_generated_videos()
        
        if len(sys.argv) > 1 and sys.argv[1] == "interactive":
            print("\n" + "=" * 60)
            choice = input("Options: (c)lean old videos, (q)uit: ").strip().lower()
            if choice == 'c':
                clean_old_videos()
