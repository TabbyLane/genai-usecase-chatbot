# GenAI Use Case Collection Chatbot (fully working mic input)

import streamlit as st
import openai
import os
import requests
import json
import gspread
from google.oauth2.service_account import Credentials
from io import BytesIO
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import tempfile

# --- Secrets ---
openai.api_key = os.getenv("OPENAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
elevenlabs_voice_id = "A84zcS5b1awkoqkNblm8"

# --- Questions ---
questions = [
    "What GenAI tool(s) did you use?",
    "How did you use it in your teaching or assessment?",
    "What were your goals or intended outcomes?",
    "What was the observed impact?",
    "What challenges or concerns did you face?",
    "What would you do differently next time?",
    "Do you have any advice for others wanting to try this?"
]

# --- Session State Init ---
if "step" not in st.session_state:
    st.session_state.step = 0
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "recording_done" not in st.session_state:
    st.session_state.recording_done = False
if "last_transcription" not in st.session_state:
    st.session_state.last_transcription = ""

# --- ElevenLabs TTS ---
def speak_text(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{elevenlabs_voice_id}"
    headers = {
        "xi-api-key": elevenlabs_api_key,
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        st.audio(BytesIO(response.content), format="audio/mp3")
    else:
        st.error("Failed to generate audio from ElevenLabs.")
        st.code(f"Status: {response.status_code}\nResponse: {response.text}")

# --- Google Sheets Setup ---
def write_usecase_to_gsheet(use_case_data):
    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT")
    if creds_json is None:
        st.error("Google service account credentials not found in secrets.")
        return

    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds)

    # Open by name
    sheet = client.open("GenAI Use Cases").worksheet("UseCases")

    # Prepare row from dict
    row = [
        str(st.session_state.get("timestamp", "")),
        use_case_data.get("What GenAI tool(s) did you use?", ""),
        use_case_data.get("How did you use it in your teaching or assessment?", ""),
        use_case_data.get("What were your goals or intended outcomes?", ""),
        use_case_data.get("What was the observed impact?", ""),
        use_case_data.get("What challenges or concerns did you face?", ""),
        use_case_data.get("What would you do differently next time?", ""),
        use_case_data.get("Do you have any advice for others wanting to try this?", ""),
        use_case_data.get("Image Caption", "")
    ]
    sheet.append_row(row, value_input_option="USER_ENTERED")

# --- Audio Processor ---
def audio_processor_callback(frame: av.AudioFrame):
    if not hasattr(st.session_state, "audio_buffer"):
        st.session_state.audio_buffer = []
    st.session_state.audio_buffer.append(frame.to_ndarray().tobytes())
    return frame

# --- Chat Display ---
st.title("🧠 GenAI Use Case Collection Chatbot")
st.write("Chat with this assistant to share how you're using GenAI in teaching and assessment.")

current_step = st.session_state.step
if current_step < len(questions):
    question = questions[current_step]
    st.markdown(f"**{question}**")
    speak_text(question)

    # Live mic input
    st.markdown("### 🎤 Speak your answer")
    audio_ctx = webrtc_streamer(
        key=f"mic_{current_step}",
        mode=WebRtcMode.SENDONLY,
        in_audio=True
    )

    if st.button("Finish Recording"):
        if hasattr(st.session_state, "audio_buffer"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                for chunk in st.session_state.audio_buffer:
                    f.write(chunk)
                f.flush()
                f.seek(0)
                transcript = openai.Audio.transcribe("whisper-1", f.name)
                response = transcript["text"]
                st.session_state.last_transcription = response
                st.session_state.responses[question] = response
                st.session_state.audio_buffer = []
                st.session_state.step += 1
                st.experimental_rerun()

    st.markdown("Or type instead:")
    typed = st.text_input("Type your response:", key=f"response_{current_step}")
    if typed:
        st.session_state.responses[question] = typed
        st.session_state.step += 1
        st.experimental_rerun()

else:
    st.success("✅ Thank you! Here's a summary of your responses:")
    st.json(st.session_state.responses)
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload a file related to your use case (e.g., screenshot, rubric, student work)", type=["png", "jpg", "jpeg", "pdf"])
    caption = st.text_input("Add a caption or description for the uploaded file")

    if st.button("Submit Use Case"):
        st.session_state["timestamp"] = datetime.utcnow().isoformat()

        use_case = st.session_state.responses.copy()
        use_case["Image Caption"] = caption

        write_usecase_to_gsheet(use_case)

        st.success("✅ Your use case has been submitted to Google Sheets!")
        st.balloons()
