from dotenv import load_dotenv
load_dotenv()
import sys
import os
import argparse
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

openai_api_key = os.getenv("OPENAI_API_KEY")


def extract_mp3(input_path):
    if not os.path.isfile(input_path):
        print(f"File not found: {input_path}")
        return
    filename, _ = os.path.splitext(os.path.basename(input_path))
    output_path = f"{filename}.mp3"
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
    if not os.path.isfile(input_video_path):
        print(f"Video file not found: {input_video_path}")
        return
    if not os.path.isfile(enhanced_wav_path):
        print(f"Enhanced WAV file not found: {enhanced_wav_path}")
        return
    filename, ext = os.path.splitext(os.path.basename(input_video_path))
    output_path = f"{filename}_enhanced{ext}"
    try:
        with VideoFileClip(input_video_path) as video:
            with AudioFileClip(enhanced_wav_path) as audio:
                video = video.set_audio(audio)
                video.write_videofile(output_path, codec='libx264', audio_codec='aac', audio_fps=44100, temp_audiofile='temp-audio.m4a', remove_temp=True)
        print(f"Video with replaced audio saved as: {output_path}")
    except Exception as e:
        print(f"Error: {e}")


def combine_videos(video1_path, video2_path, output_path):
    if not os.path.isfile(video1_path):
        print(f"First video file not found: {video1_path}")
        return
    if not os.path.isfile(video2_path):
        print(f"Second video file not found: {video2_path}")
        return
    try:
        clip1 = VideoFileClip(video1_path)
        clip2 = VideoFileClip(video2_path)
        final_clip = concatenate_videoclips([clip1, clip2])
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        print(f"Combined video saved as: {output_path}")
    except Exception as e:
        print(f"Error: {e}")


def transcribe_audio(input_path, model_name="base"):
    import whisper
    if not os.path.isfile(input_path):
        print(f"File not found: {input_path}")
        return
    try:
        model = whisper.load_model(model_name)
        print(f"Transcribing {input_path} with Whisper model '{model_name}'...")
        result = model.transcribe(input_path, task="transcribe", verbose=True)
        transcript_path = os.path.splitext(os.path.basename(input_path))[0] + ".txt"
        srt_path = os.path.splitext(os.path.basename(input_path))[0] + ".srt"
        with open(transcript_path, "w") as f:
            f.write(result["text"])
        # Save SRT
        with open(srt_path, "w") as f:
            for segment in result["segments"]:
                # SRT index
                f.write(f"{segment['id']+1}\n")
                # SRT time format
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


def main():
    parser = argparse.ArgumentParser(description="Extract MP3, replace audio, combine videos, or transcribe audio/video.")
    parser.add_argument("input_file", nargs="?", help="Input video/audio file (MKV/MP4/MP3/WAV)")
    parser.add_argument("--replace-audio", help="Enhanced WAV file to replace the original audio")
    parser.add_argument("--combine", nargs=3, metavar=("VIDEO1", "VIDEO2", "OUTPUT"), help="Combine two videos into one output file")
    parser.add_argument("--transcribe", action="store_true", help="Transcribe the input file using Whisper")
    parser.add_argument("--model", default="base", help="Whisper model to use (default: base)")
    args = parser.parse_args()
    if args.combine:
        video1, video2, output = args.combine
        combine_videos(video1, video2, output)
    elif args.replace_audio:
        replace_audio(args.input_file, args.replace_audio)
    elif args.transcribe:
        transcribe_audio(args.input_file, args.model)
    elif args.input_file:
        extract_mp3(args.input_file)
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 