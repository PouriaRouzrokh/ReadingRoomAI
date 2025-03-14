import os
import math
from dotenv import load_dotenv
from moviepy.video.io.VideoFileClip import VideoFileClip
from openai import OpenAI
from pydub import AudioSegment

# Load environment variables
load_dotenv()

def extract_audio(video_path, output_dir, full_audio_path=None, force_extract=False):
    """
    Extract audio from a video file and save it as an MP3.
    """
    try:
        # Ensure output directory exists
        if full_audio_path is None:
            full_audio_path = os.path.join(output_dir, "audio_full.mp3")

        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        ### Check if the video file exists
        assert os.path.exists(video_path), f"Video file not found: {video_path}"

        ### Check if the audio file already exists
        if os.path.exists(full_audio_path):
            if not force_extract:
                print(f"Skipping extraction as the audio file already exists: {full_audio_path}")
                return True
            else:
                print(f"Audio file already exists. Overwriting: {full_audio_path}")
                os.remove(full_audio_path)
        
        # Load the video file
        video = VideoFileClip(video_path)
        
        # Extract the audio
        audio = video.audio
        
        # Write the audio to an MP3 file
        audio.write_audiofile(full_audio_path, codec='mp3')
        
        # Close the video and audio objects to release resources
        audio.close()
        video.close()
        
        print(f"Successfully extracted audio to {full_audio_path}")
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

def split_audio(audio_path, output_dir, chunk_duration, save_chunks=True):
    """
    Split an audio file into chunks of specified duration in seconds.
    
    Args:
        audio_path (str): Path to the audio file.
        output_dir (str): Directory to save the chunked audio files.
        chunk_duration (int): Duration of each chunk in seconds.
        save_chunks (bool): Whether to save the audio chunks to disk.
        
    Returns:
        list: List of paths to the chunked audio files and their start times in seconds.
    """
    try:
        # Create chunks directory if it doesn't exist and if we're saving chunks
        chunks_dir = os.path.join(output_dir, "audio_chunks")
        if save_chunks and not os.path.exists(chunks_dir):
            os.makedirs(chunks_dir)
            
        # Load the audio file
        audio = AudioSegment.from_file(audio_path)
        
        # Get the total duration in milliseconds
        total_duration = len(audio)
        
        # Convert chunk_duration from seconds to milliseconds
        chunk_duration_ms = chunk_duration * 1000
        
        # Calculate the number of chunks
        num_chunks = math.ceil(total_duration / chunk_duration_ms)
        
        chunk_info = []  # Will store (path, start_time_seconds) tuples
        
        # Split the audio and save chunks
        for i in range(num_chunks):
            # Calculate start and end times for this chunk
            start_time = i * chunk_duration_ms
            end_time = min((i + 1) * chunk_duration_ms, total_duration)
            
            # Define the output path for this chunk
            chunk_filename = f"chunk_{i+1}.mp3"
            
            if save_chunks:
                chunk_path = os.path.join(chunks_dir, chunk_filename)
                
                # Check if the chunk already exists
                if os.path.exists(chunk_path):
                    print(f"Chunk file already exists: {chunk_path}")
                    chunk_info.append((chunk_path, start_time / 1000))  # Convert to seconds
                    continue
                    
                # Extract the chunk
                chunk = audio[start_time:end_time]
                
                # Export the chunk
                chunk.export(chunk_path, format="mp3")
                
                # Add the path and start time to our list
                chunk_info.append((chunk_path, start_time / 1000))  # Convert to seconds
            else:
                # If not saving, create a temporary file
                temp_dir = os.path.join(output_dir, "temp")
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                
                chunk_path = os.path.join(temp_dir, f"temp_chunk_{i+1}.mp3")
                
                # Extract the chunk
                chunk = audio[start_time:end_time]
                
                # Export the chunk
                chunk.export(chunk_path, format="mp3")
                
                # Add the path and start time to our list
                chunk_info.append((chunk_path, start_time / 1000))  # Convert to seconds
        
        return chunk_info
    
    except Exception as e:
        print(f"Error splitting audio: {str(e)}")
        return []

# Function to adjust timestamps in transcription based on chunk start time
def adjust_timestamps(transcription, start_time_seconds):
    """
    Adjust timestamps in the transcription to reflect the absolute position in the full audio.
    
    Args:
        transcription (str): Processed transcription text with timestamps in [H:MM:SS] format.
        start_time_seconds (float): Start time of the chunk in seconds.
        
    Returns:
        str: Transcription with adjusted timestamps.
    """
    lines = transcription.split('\n')
    adjusted_lines = []
    
    for line in lines:
        if line.startswith('['):
            # Extract the timestamp
            timestamp_end = line.find(']')
            timestamp = line[1:timestamp_end]
            text = line[timestamp_end+1:]
            
            # Parse the timestamp
            parts = timestamp.split(':')
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                
                # Convert to seconds
                timestamp_seconds = hours * 3600 + minutes * 60 + seconds
                
                # Add the start time of the chunk
                adjusted_seconds = timestamp_seconds + start_time_seconds
                
                # Convert back to hours:minutes:seconds
                adjusted_hours = int(adjusted_seconds // 3600)
                adjusted_minutes = int((adjusted_seconds % 3600) // 60)
                adjusted_seconds = int(adjusted_seconds % 60)
                
                # Format the adjusted timestamp
                adjusted_timestamp = f"{adjusted_hours}:{adjusted_minutes:02d}:{adjusted_seconds:02d}"
                
                # Reconstruct the line
                adjusted_line = f"[{adjusted_timestamp}]{text}"
                adjusted_lines.append(adjusted_line)
            else:
                # If the timestamp format is unexpected, keep the original line
                adjusted_lines.append(line)
        else:
            # If the line doesn't start with a timestamp, keep it as is
            adjusted_lines.append(line)
    
    return '\n'.join(adjusted_lines)

# Function to transcribe audio using OpenAI's transcription service
def transcribe_audio(full_audio_path=None, output_dir=None, chunk_duration=None, save_audio_chunks=True, save_chunk_transcripts=True):
    """
    Transcribe audio file using OpenAI's API. If chunk_duration is provided,
    the audio is split into chunks before transcription.
    
    Args:
        full_audio_path (str, optional): Path to the full audio file.
        output_dir (str, optional): Directory to save the transcriptions and audio chunks.
        chunk_duration (int, optional): Duration of each chunk in seconds.
        save_audio_chunks (bool): Whether to save the audio chunks.
        save_chunk_transcripts (bool): Whether to save individual chunk transcriptions.
        
    Returns:
        str: The full transcription text.
    """
    # Get API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # If no output directory is specified, use the directory of the audio file
    if output_dir is None:
        output_dir = os.path.dirname(full_audio_path)
    elif full_audio_path is None:
        full_audio_path = os.path.join(output_dir, "audio_full.mp3")
    else:
        assert os.path.exists(full_audio_path), f"Audio file not found: {full_audio_path}"
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Path for the full transcription
    full_transcription_path = os.path.join(output_dir, "full_transcription.txt")
    
    # Check if full transcription already exists
    if os.path.exists(full_transcription_path):
        print(f"Full transcription already exists: {full_transcription_path}")
        with open(full_transcription_path, "r", encoding="utf-8") as f:
            return f.read()
    
    # If chunk_duration is not provided, transcribe the entire audio file
    if chunk_duration is None or chunk_duration <= 0:
        with open(full_audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file, 
                response_format="srt"
            )
            processed_transcription = process_transcription(transcription)
            
            # Save the full transcription
            with open(full_transcription_path, "w", encoding="utf-8") as f:
                f.write(processed_transcription)
            
            return processed_transcription
    
    # Split the audio into chunks - now returns list of (path, start_time_seconds) tuples
    chunk_info = split_audio(full_audio_path, output_dir, chunk_duration, save_audio_chunks)
    
    # Create directory for chunk transcripts if needed
    transcripts_dir = None
    if save_chunk_transcripts:
        transcripts_dir = os.path.join(output_dir, "chunk_transcripts")
        if not os.path.exists(transcripts_dir):
            os.makedirs(transcripts_dir)
    
    # Initialize the full transcription
    full_transcription = ""
    
    # Transcribe each chunk
    for i, (chunk_path, start_time_seconds) in enumerate(chunk_info):
        chunk_num = i + 1
        
        # Path for individual chunk transcription
        chunk_transcript_path = None
        if save_chunk_transcripts:
            chunk_transcript_path = os.path.join(transcripts_dir, f"chunk_{chunk_num}_transcript.txt")
        
        # Add separator at the beginning of the chunk
        chunk_header = f"==== Beginning of Part {chunk_num} ====\n"
        full_transcription += chunk_header
        
        # Check if chunk transcript already exists
        if save_chunk_transcripts and os.path.exists(chunk_transcript_path):
            print(f"Chunk transcript already exists: {chunk_transcript_path}")
            with open(chunk_transcript_path, "r", encoding="utf-8") as f:
                chunk_content = f.read()
                # Extract just the transcript part (between header and footer)
                start_idx = chunk_content.find(chunk_header) + len(chunk_header)
                end_idx = chunk_content.find(f"==== Ending of Part {chunk_num} ====")
                if end_idx > start_idx:
                    processed_chunk_transcription = chunk_content[start_idx:end_idx].strip()
                    full_transcription += processed_chunk_transcription + "\n"
        else:
            # Transcribe the chunk
            with open(chunk_path, "rb") as audio_file:
                try:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file, 
                        response_format="srt"
                    )
                    processed_chunk_transcription = process_transcription(transcription)
                    
                    # Adjust timestamps to reflect position in full audio
                    adjusted_transcription = adjust_timestamps(processed_chunk_transcription, start_time_seconds)
                    
                    # Add the processed chunk transcription to the full transcription
                    full_transcription += adjusted_transcription + "\n"
                    
                    # Save individual chunk transcription if requested
                    if save_chunk_transcripts and chunk_transcript_path:
                        with open(chunk_transcript_path, "w", encoding="utf-8") as f:
                            f.write(chunk_header + adjusted_transcription + "\n" + f"==== Ending of Part {chunk_num} ====")
                    
                except Exception as e:
                    error_msg = f"Error transcribing chunk {chunk_num}: {str(e)}\n"
                    print(error_msg)
                    full_transcription += error_msg
        
        # Add separator at the end of the chunk
        chunk_footer = f"==== Ending of Part {chunk_num} ====\n\n"
        full_transcription += chunk_footer
        
        # Remove temporary files if not saving chunks
        if not save_audio_chunks and "temp" in chunk_path:
            try:
                os.remove(chunk_path)
            except:
                pass
    
    # If we created a temp directory and aren't saving chunks, try to remove it
    if not save_audio_chunks:
        temp_dir = os.path.join(output_dir, "temp")
        try:
            if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                os.rmdir(temp_dir)
        except:
            pass
    
    # Save the full transcription
    with open(full_transcription_path, "w", encoding="utf-8") as f:
        f.write(full_transcription)
    
    return full_transcription