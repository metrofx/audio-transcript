import whisper
from pydub import AudioSegment
import os
import datetime
import sys
import time
import requests
from dotenv import load_dotenv

def convert_m4a_to_wav(m4a_path, wav_path):
    if os.path.exists(wav_path):
        print(f"{wav_path} already exists. Skipping conversion.")
        return
    try:
        # sound = AudioSegment.from_m4a(m4a_path)
        sound = AudioSegment.from_file(m4a_path, format= 'm4a')
        sound.export(wav_path, format="wav")
        print("Conversion to WAV successful.")
    except Exception as e:
        print(f"Error during conversion: {e}")

def transcribe_audio_to_srt(wav_path, srt_path, model_name='large-v2', context=None):
    duration_start_time = time.time()
    try:
        model = whisper.load_model(model_name)
        options = {}

        if context:
            options['prompt'] = context

        result = model.transcribe(wav_path, **options)

        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(result['segments']):
                start_time = str(datetime.timedelta(seconds=int(segment['start']))).split(".")[0]
                end_time = str(datetime.timedelta(seconds=int(segment['end']))).split(".")[0]
                f.write(f"{i + 1}\n")
                f.write(f"{start_time},000 --> {end_time},000\n")
                f.write(f"{segment['text']}\n\n")

        print(f"Transcription saved to {srt_path}")
    except Exception as e:
        print(f"An error occurred during transcription: {e}")
    duration_end_time = time.time()
    duration_minutes = (duration_end_time - duration_start_time) / 60
    return duration_minutes

def send_mattermost_message(webhook_url, message):
    payload = {"username": "transcriber-bot", "text": message}
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print("Message sent to Mattermost successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Mattermost: {e}")

        
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python whisper_v1.py <audio_path_m4a> <audio_path_wav>")
        sys.exit(1)

    # Read paths from command line arguments
    audio_path_m4a = sys.argv[1]
    audio_path_wav = sys.argv[2]
    mm_webhook_url = os.getenv("MM_WEBHOOK_URL")
    srt_path = os.path.splitext(audio_path_m4a)[0] + ".srt"

    # Convert m4a to WAV
    #convert_m4a_to_wav(audio_path_m4a, audio_path_wav)

    # Context instructions (custom vocabulary)
    context = os.getenv("CONTEXT")

    # Transcribe the audio and save as SRT, measure duration
    duration_minutes = transcribe_audio_to_srt(audio_path_wav, srt_path, context=context)

    # Send duration to Mattermost
    message = f"Transcription of {audio_path_m4a} completed in {duration_minutes:.2f} minutes."
    send_mattermost_message(mm_webhook_url, message)
