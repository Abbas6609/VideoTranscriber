import streamlit as st
from pytube import YouTube
import whisper
import os
import re
import torch
from fpdf import FPDF
import moviepy.editor as mp
from datetime import datetime
import base64

# Convert image to base64 to use in HTML/CSS background
def get_base64_encoded_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

# Path to your image
image_path = 'Bg.png'
encoded_image = get_base64_encoded_image(image_path)

# Set the background image using Markdown with custom HTML/CSS
background_style = f"""
<style>
    .stApp {{
        background-image: url("data:image/png;base64,{encoded_image}");
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center;
    }}
    /* Additional CSS for title styling */
    .reportview-container .markdown-text-container h1 {{
        color: lawngreen;
    }}
</style>
"""
st.markdown(background_style, unsafe_allow_html=True)

# App name and head title with size customization
st.markdown('<h1 style="color: lawngreen; font-size: 55px;">🎬📑 Tosief\'s Reel to Paper</h1>', unsafe_allow_html=True)


st.sidebar.title('Video Transcription App')

def extract_video_id(url):
    """Extract the video ID from the YouTube URL."""
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    if match:
        return match.group(1)
    raise ValueError("Invalid YouTube URL")

def download_or_extract_audio(source):
    """Determine if source is a URL or a file path, and extract audio accordingly."""
    if "http" in source:
        yt = YouTube(source)
        audio_stream = yt.streams.filter(only_audio=True).first()
        out_file = audio_stream.download(output_path=".")
        new_file = os.path.splitext(out_file)[0] + '.mp3'
        os.rename(out_file, new_file)
        return new_file
    else:
        video = mp.VideoFileClip(source)
        audio_file = os.path.splitext(source)[0] + ".mp3"
        if os.path.exists(audio_file):
            os.remove(audio_file)  # Ensure the file does not exist before writing
        video.audio.write_audiofile(audio_file)
        return audio_file

def transcribe_audio(file_path):
    """Transcribe the audio file using the Whisper model."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model("base", device=device)
    options = {"language": "en", "fp16": torch.cuda.is_available()}
    result = model.transcribe(file_path, **options)
    os.remove(file_path)  # Remove the mp3 file after transcription
    return result['text']

def save_transcript(transcript, filename):
    """Save the transcript to a PDF file."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size = 12)
    pdf.multi_cell(0, 10, transcript)
    pdf.output(filename)
    return filename

selection = st.sidebar.radio("Choose the source of the video:", ('YouTube URL', 'Local Video File'))

if selection == 'YouTube URL':
    url = st.sidebar.text_input("Enter the YouTube URL:")
    if st.sidebar.button('Process Video/Audio', key='youtube') and url:
        try:
            video_id = extract_video_id(url)
            with st.spinner('Processing...'):
                audio_file = download_or_extract_audio(url)
                if audio_file:
                    transcript = transcribe_audio(audio_file)
                    file_path = save_transcript(transcript, f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_Transcription.pdf")
                    st.sidebar.success("Transcription completed successfully!")
                    with open(file_path, "rb") as f:
                        st.sidebar.download_button('Download Transcript PDF', f, file_name=file_path)
        except Exception as e:
            st.sidebar.error(f"An error occurred: {e}")
elif selection == 'Local Video File':
    uploaded_file = st.sidebar.file_uploader("Upload a video file:", type=['mp4', 'mkv', 'avi'])
    if uploaded_file is not None and st.sidebar.button('Process Video/Audio', key='local'):
        file_path = os.path.join(".", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        with st.spinner('Processing...'):
            audio_file = download_or_extract_audio(file_path)
            if audio_file:
                transcript = transcribe_audio(audio_file)
                file_path = save_transcript(transcript, f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_Transcription.pdf")
                st.sidebar.success("Transcription completed successfully!")
                with open(file_path, "rb") as f:
                    st.sidebar.download_button('Download Transcript PDF', f, file_name=file_path)