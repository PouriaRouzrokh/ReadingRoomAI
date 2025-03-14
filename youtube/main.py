import os
from tools.audio_processing import extract_audio, transcribe_audio

VIDEO_PATH = "/Users/pouria/Documents/Coding/ReadingRoomAI/data/Mar_9/Mar_19.mp4"
OUTPUT_DIR = "/Users/pouria/Documents/Coding/ReadingRoomAI/data/Mar_9"

def main():

    ### Extract audio from video
    extract_audio(VIDEO_PATH, OUTPUT_DIR)

    ### Transcribe audio
    transcribe_audio(
        output_dir=OUTPUT_DIR, 
        chunk_duration=600, 
        save_audio_chunks=True, 
        save_chunk_transcripts=True
    )

if __name__ == "__main__":
    main()






