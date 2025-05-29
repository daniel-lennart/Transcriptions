# Lesson Processing Pipeline

A Python script for processing lesson videos: extract MP3, replace audio, combine videos, transcribe with Whisper, clean SRT subtitles with OpenAI, and convert SRT to clean text. All outputs are organized into a structured folder hierarchy for easy management.

## Features
- Extract MP3 audio from video files
- Replace video audio with enhanced WAV
- Combine multiple video files
- Transcribe audio/video to text and SRT using Whisper
- Clean SRT subtitles using OpenAI API (remove filler words, correct misinterpretations)
- Convert SRT subtitles to clean text/markdown
- **Auto-organizes all outputs into subfolders**

## File Structure
```
Transcriptions/
│
├── lesson_pipeline.py
├── requirements.txt
├── README.md
├── .env
│
├── data/
│   ├── raw_videos/           # Original MP4/MKV files
│   ├── enhanced_audio/       # Enhanced WAV files
│   ├── processed_videos/     # Videos with replaced audio, combined videos
│   └── mp3/                  # Extracted MP3s
│
├── transcripts/
│   ├── srt/                  # All SRT files (original and cleaned)
│   ├── txt/                  # All plain text/markdown transcripts
│   └── diffs/                # Diffs between original and cleaned SRTs
│
└── utils/                    # (Optional) Python modules for helper functions
```

**All folders are auto-created by the script if they do not exist.**

## Setup
1. Clone the repository and navigate to the project folder.
2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-...
   ```

## Usage Examples

### Place your files:
- Put original videos in `data/raw_videos/`
- Put enhanced audio in `data/enhanced_audio/`

### Extract MP3 from Video
```bash
python lesson_pipeline.py data/raw_videos/my_video.mp4
# Output: data/mp3/my_video.mp3
```

### Replace Audio in Video
```bash
python lesson_pipeline.py data/raw_videos/my_video.mp4 --replace-audio data/enhanced_audio/enhanced_audio.wav
# Output: data/processed_videos/my_video_enhanced.mp4
```

### Combine Two Videos
```bash
python lesson_pipeline.py --combine data/raw_videos/video1.mp4 data/raw_videos/video2.mp4 combined.mp4
# Output: data/processed_videos/combined.mp4
```

### Transcribe Video/Audio to Text and SRT
```bash
python lesson_pipeline.py data/processed_videos/combined.mp4 --transcribe --model turbo
# Output: transcripts/txt/combined.txt and transcripts/srt/combined.srt
```

### Clean SRT with OpenAI API (uses built-in prompt by default)
```bash
python lesson_pipeline.py --clean-srt transcripts/srt/combined.srt transcripts/srt/combined_cleaned.srt
# Output: transcripts/srt/combined_cleaned.srt
```
Or use a prompt file:
```bash
python lesson_pipeline.py --clean-srt transcripts/srt/combined.srt transcripts/srt/combined_cleaned.srt --prompt prompt.txt
```

### Convert SRT to Clean Text/Markdown
```bash
python lesson_pipeline.py --srt-to-text transcripts/srt/combined_cleaned.srt transcripts/txt/combined_cleaned.md
# Output: transcripts/txt/combined_cleaned.md
```

## Function Descriptions
- `extract_mp3(input_path)`: Extracts MP3 audio from a video file.
- `replace_audio(input_video_path, enhanced_wav_path)`: Replaces the audio in a video file with an enhanced WAV file.
- `combine_videos(video1_path, video2_path, output_path)`: Combines two video files into one.
- `transcribe_audio(input_path, model_name)`: Transcribes audio/video to text and SRT using Whisper.
- `clean_srt_with_openai(srt_path, output_srt_path, prompt)`: Cleans SRT subtitles using OpenAI API.
- `srt_to_text(srt_path, output_txt_path)`: Converts SRT subtitles to clean text/markdown.

## Notes
- The script is designed for lesson and tutorial processing, especially for topics like AI agents, Make.com, n8n, langflow, vector embeddings, and GPT.
- For best results, use the turbo or gpt-4.1-mini model for fast transcription and the provided prompt for SRT cleaning.
- All outputs are organized for you—no manual sorting needed! 