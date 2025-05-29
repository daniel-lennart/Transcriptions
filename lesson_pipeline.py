import sys
import os
import argparse
from dotenv import load_dotenv
load_dotenv()
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import openai
import re

openai_api_key = os.getenv("OPENAI_API_KEY")

# Directory structure
RAW_VIDEO_DIR = "data/raw_videos"
ENHANCED_AUDIO_DIR = "data/enhanced_audio"
PROCESSED_VIDEO_DIR = "data/processed_videos"
MP3_DIR = "data/mp3"
SRT_DIR = "transcripts/srt"
TXT_DIR = "transcripts/txt"
DIFFS_DIR = "transcripts/diffs"

# Ensure directories exist
for d in [RAW_VIDEO_DIR, ENHANCED_AUDIO_DIR, PROCESSED_VIDEO_DIR, MP3_DIR, SRT_DIR, TXT_DIR, DIFFS_DIR]:
    os.makedirs(d, exist_ok=True)

DEFAULT_CLEAN_SRT_PROMPT = """
Process video transcripts by removing filler words and correcting misinterpreted words related to AI agents, Make.com, n8n, langflow, vector embeddings, and GPT. Ensure the main content remains intact.

# Steps
1. **Identify Filler Words**: Identify common filler words such as "uh," "um," "erm"  etc., and remove them from the transcript.
2. **Correct Misinterpreted Words**: Analyze the context of the sentence, especially focusing on your key topics, and correct any misinterpreted words to ensure clarity and accuracy.
3. **Maintain Contextual Integrity**: Ensure that the removal of filler words and correction of misinterpreted words do not alter the meaning or the flow and timing of the original text.

# Output Format
- Provide the revised transcript in a clean, well-structured paragraph format, free of filler words and errors.
- Keep the timings in case of srt files
- Ensure the document is easy to read, with natural language flow.

# Notes
- Pay special attention to the topics of AI agents, Make.com, n8n, langflow, vector embeddings, and GPT when correcting misinterpreted words, ensuring these terms are accurately represented.
- Ensure the resulting text remains conversational and comprehensible.
"""


def extract_mp3(input_path):
    """Extract MP3 audio from a video file."""
    if not os.path.isfile(input_path):
        print(f"File not found: {input_path}")
        return
    filename, _ = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(MP3_DIR, f"{filename}.mp3")
    try:
        with VideoFileClip(input_path) as video:
            audio = video.audio
            if audio is None:
                print("No audio stream found in the video.")
                return
            audio.write_audiofile(output_path, codec='mp3')
        print(f"Extracted MP3 saved as: {output_path}")
    except Exception as e:
        print(f"Error: {e}")


def replace_audio(input_video_path, enhanced_wav_path):
    """Replace the audio in a video file with an enhanced WAV file."""
    if not os.path.isfile(input_video_path):
        print(f"Video file not found: {input_video_path}")
        return
    if not os.path.isfile(enhanced_wav_path):
        print(f"Enhanced WAV file not found: {enhanced_wav_path}")
        return
    filename, ext = os.path.splitext(os.path.basename(input_video_path))
    output_path = os.path.join(PROCESSED_VIDEO_DIR, f"{filename}_enhanced{ext}")
    try:
        with VideoFileClip(input_video_path) as video:
            with AudioFileClip(enhanced_wav_path) as audio:
                video = video.set_audio(audio)
                video.write_videofile(output_path, codec='libx264', audio_codec='aac', audio_fps=44100, temp_audiofile='temp-audio.m4a', remove_temp=True)
        print(f"Video with replaced audio saved as: {output_path}")
    except Exception as e:
        print(f"Error: {e}")


def combine_videos(video1_path, video2_path, output_path=None):
    """Combine two video files into one."""
    if not os.path.isfile(video1_path):
        print(f"First video file not found: {video1_path}")
        return
    if not os.path.isfile(video2_path):
        print(f"Second video file not found: {video2_path}")
        return
    if output_path is None:
        output_path = os.path.join(PROCESSED_VIDEO_DIR, "combined.mp4")
    else:
        output_path = os.path.join(PROCESSED_VIDEO_DIR, os.path.basename(output_path))
    try:
        clip1 = VideoFileClip(video1_path)
        clip2 = VideoFileClip(video2_path)
        final_clip = concatenate_videoclips([clip1, clip2])
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        print(f"Combined video saved as: {output_path}")
    except Exception as e:
        print(f"Error: {e}")


def transcribe_audio(input_path, model_name="base"):
    """Transcribe audio or video file to text and SRT using Whisper."""
    import whisper
    if not os.path.isfile(input_path):
        print(f"File not found: {input_path}")
        return
    filename, _ = os.path.splitext(os.path.basename(input_path))
    transcript_path = os.path.join(TXT_DIR, f"{filename}.txt")
    srt_path = os.path.join(SRT_DIR, f"{filename}.srt")
    try:
        model = whisper.load_model(model_name)
        print(f"Transcribing {input_path} with Whisper model '{model_name}'...")
        result = model.transcribe(input_path, task="transcribe", verbose=True)
        with open(transcript_path, "w") as f:
            f.write(result["text"])
        # Save SRT
        with open(srt_path, "w") as f:
            for segment in result["segments"]:
                f.write(f"{segment['id']+1}\n")
                start = segment['start']
                end = segment['end']
                f.write(f"{format_srt_time(start)} --> {format_srt_time(end)}\n")
                f.write(segment['text'].strip() + "\n\n")
        print(f"Transcript saved as: {transcript_path}")
        print(f"SRT saved as: {srt_path}")
    except Exception as e:
        print(f"Error: {e}")


def format_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def clean_srt_with_openai(srt_path, output_srt_path, prompt=None):
    """Send SRT to OpenAI API for cleaning and correction."""
    if prompt is None:
        prompt = DEFAULT_CLEAN_SRT_PROMPT
    with open(srt_path, "r") as f:
        srt_content = f.read()
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": srt_content}
        ],
        temperature=0.2
    )
    cleaned_srt = response.choices[0].message.content
    with open(output_srt_path, "w") as f:
        f.write(cleaned_srt)
    print(f"Cleaned SRT saved as: {output_srt_path}")
    return output_srt_path


def srt_to_text(srt_path, output_txt_path):
    """Convert SRT file to clean text by removing timings and indices."""
    with open(srt_path, "r") as f:
        srt_content = f.read()
    # Remove SRT index and timings
    text = re.sub(r"\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n", "", srt_content)
    # Remove empty lines
    text = re.sub(r"\n{2,}", "\n", text)
    with open(output_txt_path, "w") as f:
        f.write(text.strip())
    print(f"Text transcript saved as: {output_txt_path}")
    return output_txt_path


def main():
    parser = argparse.ArgumentParser(description="Lesson Processing Pipeline: Extract MP3, replace audio, combine videos, transcribe, clean SRT, and convert to text.")
    parser.add_argument("input_file", nargs="?", help="Input video/audio file (MKV/MP4/MP3/WAV)")
    parser.add_argument("--replace-audio", help="Enhanced WAV file to replace the original audio")
    parser.add_argument("--combine", nargs=3, metavar=("VIDEO1", "VIDEO2", "OUTPUT"), help="Combine two videos into one output file")
    parser.add_argument("--transcribe", action="store_true", help="Transcribe the input file using Whisper")
    parser.add_argument("--model", default="base", help="Whisper model to use (default: base)")
    parser.add_argument("--clean-srt", nargs=2, metavar=("SRT", "OUTPUT_SRT"), help="Clean SRT file with OpenAI API and save to output SRT")
    parser.add_argument("--prompt", default=None, help="Prompt file or string for OpenAI cleaning")
    parser.add_argument("--srt-to-text", nargs=2, metavar=("SRT", "OUTPUT_TXT"), help="Convert SRT file to clean text")
    args = parser.parse_args()

    if args.combine:
        video1, video2, output = args.combine
        combine_videos(video1, video2, output)
    elif args.replace_audio:
        replace_audio(args.input_file, args.replace_audio)
    elif args.transcribe:
        transcribe_audio(args.input_file, args.model)
    elif args.clean_srt:
        srt_path, output_srt_path = args.clean_srt
        clean_srt_with_openai(srt_path, output_srt_path, args.prompt)
    elif args.srt_to_text:
        srt_path, output_txt_path = args.srt_to_text
        srt_to_text(srt_path, output_txt_path)
    elif args.input_file:
        extract_mp3(args.input_file)
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 