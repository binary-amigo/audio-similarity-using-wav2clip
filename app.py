import streamlit as st
import requests
from streamlit_webrtc import AudioProcessorBase, RTCConfiguration
import tempfile
import os
import numpy as np
import soundfile as sf

# Backend URL
BACKEND_URL = "http://127.0.0.1:5000"  # Replace with your backend URL if hosted elsewhere

# Page Title
st.title("Audio Similarity Checker")
st.write("Upload or record an audio file to find similar audio in our database.")

# Options: Upload or Record Audio
audio_option = st.radio("Choose how to provide audio:", ("Upload Audio", "Record Audio"))

uploaded_audio = None
recorded_audio_path = None

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_data = []
    
    def recv(self, frame):
        """Process incoming audio frames."""
        if frame is not None:
            audio_data = frame.to_ndarray()
            self.audio_data.append(audio_data)
            # Save the data into session to use it later
            st.session_state.audio_data = np.concatenate(self.audio_data, axis=0)
        return frame

# Handle Audio Upload
if audio_option == "Upload Audio":
    uploaded_audio = st.file_uploader("Upload an Audio File", type=["wav", "mp3", "flac", "ogg"])

# Handle Audio Recording
elif audio_option == "Record Audio":
    uploaded_audio = st.audio_input("Record")

# Show uploaded audio playback
if uploaded_audio:
    st.audio(uploaded_audio, format="audio/wav")

# Compare Audio Button
if st.button("Compare Audio"):
    audio_to_compare = None

    # Determine which audio to use (uploaded or recorded)
    if uploaded_audio:
        # Save uploaded audio temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(uploaded_audio.getvalue())
            audio_to_compare = temp_audio.name
    elif "audio_data" in st.session_state:
        # Save recorded audio temporarily
        audio_data = st.session_state.audio_data
        recorded_audio_path = "recorded_audio.wav"
        sf.write(recorded_audio_path, audio_data, 16000)  # Adjust the sample rate as necessary
        audio_to_compare = recorded_audio_path

    if audio_to_compare:
        # Send the audio file to the backend
        with st.spinner("Comparing audio..."):
            with open(audio_to_compare, "rb") as audio_file:
                files = {"file": audio_file}
                response = requests.post(f"{BACKEND_URL}/find_match", files=files)

        # Handle backend response
        if response.status_code == 200:
            result = response.json()
            if result["match_found"]:
                st.success(f"Match found! Similar Audio ID: {result['match_id']}, Similarity Score: {result['similarity']:.2f}")
                matched_audio_path = os.path.join("audio_database", result["match_id"])
                if os.path.exists(matched_audio_path):
                    st.audio(matched_audio_path, format="audio/wav")
                else:
                    st.warning("Matched audio file not found in the database.")
            else:
                st.warning("No similar audio found.")
        else:
            st.error(f"Error: {response.json().get('error')}")

        # Clean up temporary file
        if os.path.exists(audio_to_compare):
            os.remove(audio_to_compare)
    else:
        st.warning("Please provide an audio file to compare.")


