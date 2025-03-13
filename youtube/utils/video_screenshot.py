from contextlib import redirect_stdout, redirect_stderr
from moviepy.video.io.VideoFileClip import VideoFileClip
import numpy as np
import os
from PIL import Image

def VideoScreenshotTool(video_path, time_str):
    """
    Extract a screenshot from a video at a specific timestamp.
    
    Args:
        video_path (str): Path to the MP4 video file
        time_str (str): Timestamp in "HH:MM:SS" format
        
    Returns:
        PIL.Image: Screenshot image at the specified timestamp
        
    Example:
        screenshot = get_video_screenshot("my_video.mp4", "01:02:45")
        screenshot.save("screenshot.jpg")
    """
    # Check if file exists
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Parse the time string to get seconds
    try:
        time_parts = time_str.split(':')
        if len(time_parts) == 3:
            hours, minutes, seconds = map(int, time_parts)
            time_seconds = hours * 3600 + minutes * 60 + seconds
        elif len(time_parts) == 2:
            # For backward compatibility, still support MM:SS format
            minutes, seconds = map(int, time_parts)
            time_seconds = minutes * 60 + seconds
        else:
            raise ValueError("Time must be in 'HH:MM:SS' or 'MM:SS' format")
    except ValueError:
        raise ValueError("Time must be in 'HH:MM:SS' or 'MM:SS' format")
    
    try:
        # Load the video silently
        with open(os.devnull, 'w') as devnull:
            with redirect_stdout(devnull), redirect_stderr(devnull):
                clip = VideoFileClip(video_path)
        
        # Check if the requested time exceeds video duration
        if time_seconds > clip.duration:
            duration_hours = int(clip.duration // 3600)
            duration_minutes = int((clip.duration % 3600) // 60)
            duration_seconds = int(clip.duration % 60)
            duration_str = f"{duration_hours:02d}:{duration_minutes:02d}:{duration_seconds:02d}"
            raise ValueError(f"Requested time {time_str} exceeds video duration of {duration_str}")
        
        # Get the frame at the specified time
        with open(os.devnull, 'w') as devnull:
            with redirect_stdout(devnull), redirect_stderr(devnull):
                frame = clip.get_frame(time_seconds)
        
        # Convert the numpy array to a PIL Image
        screenshot = Image.fromarray(np.uint8(frame))
        
        # Close the video file
        clip.close()
        
        return screenshot
    
    except Exception as e:
        raise Exception(f"Error extracting screenshot: {str(e)}")
