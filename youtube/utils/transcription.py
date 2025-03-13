import os
from dotenv import load_dotenv
from moviepy.video.io.VideoFileClip import VideoFileClip
from openai import OpenAI

# Load environment variables
load_dotenv()

def extract_audio(video_path, output_path):
    """
    Extract audio from a video file and save it as an MP3.
    """
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Load the video file
        video = VideoFileClip(video_path)
        
        # Extract the audio
        audio = video.audio
        
        # Write the audio to an MP3 file
        audio.write_audiofile(output_path, codec='mp3')
        
        # Close the video and audio objects to release resources
        audio.close()
        video.close()
        
        print(f"Successfully extracted audio to {output_path}")
        return True
    
    except Exception as e:
        print(f"Error extracting audio: {str(e)}")
        return False

def format_time(time_str):
    """
    Convert time format from "00:00:00,000" to "0:00:00"
    """
    # Split by comma and get the first part (hours:minutes:seconds)
    hours_mins_secs = time_str.split(',')[0]
    
    # Split by colon to get hours, minutes, seconds
    parts = hours_mins_secs.split(':')
    
    # Remove leading zero from hours if it's not necessary
    hours = str(int(parts[0]))
    
    return f"{hours}:{parts[1]}:{parts[2]}"

# Function to process the raw transcription into the desired format
def process_transcription(transcription):
    """
    Process SRT format transcription into a simpler format
    """
    blocks = transcription.split('\n\n')
    processed_lines = []
    
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            time_range = lines[1]
            text = lines[2]
            start_time = time_range.split(' --> ')[0]
            # Convert the time format from "00:00:00,000" to "0:00:00"
            formatted_start_time = format_time(start_time)
            processed_line = f"[{formatted_start_time}]{text}"
            processed_lines.append(processed_line)
    
    return '\n'.join(processed_lines)

# Function to transcribe audio using OpenAI's transcription service
def transcribe_audio(file_path):
    """
    Transcribe audio file using OpenAI's API
    """
    # Get API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file, 
            response_format="srt"
        )
        # Pass the transcription directly for processing
        return process_transcription(transcription)

def transcribe_video(video_path, output_path, temp_path="./temp"):
    """
    Extract transcription from a video file and save it as a text file.
    """
    try:
        # Extract audio from the video
        audio_path = os.path.join(temp_path, "temp_audio.mp3")
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)
        if not extract_audio(video_path, audio_path):
            return False
        
        # Transcribe the extracted audio
        transcription = transcribe_audio(audio_path)
        
        # Save the transcription to a text file
        with open(output_path, 'w') as file:
            file.write(transcription)
        
        # Remove the temporary audio file
        os.remove(audio_path)
        
        print(f"Successfully transcribed video to {output_path}")
        return True
    
    except Exception as e:
        print(f"Error transcribing video: {str(e)}")
        return False