# GenAI Use Case Collection Chatbot (with ElevenLabs TTS + Whisper STT)

import streamlit as st
import openai
import os
import requests
from io import BytesIO

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

# --- Chat Display ---
st.title("🧠 GenAI Use Case Collection Chatbot")
st.write("Chat with this assistant to share how you're using GenAI in teaching and assessment.")

current_step = st.session_state.step
if current_step < len(questions):
    question = questions[current_step]
    st.markdown(f"**{question}**")
    speak_text(question)

    # Text input fallback
    response = st.text_input("Type your response:", key=f"response_{current_step}")

    # Voice upload + Whisper transcription
    st.markdown("Or upload a spoken response (MP3 or WAV):")
    audio_file = st.file_uploader("Upload your voice response", type=["mp3", "wav"], key=f"audio_{current_step}")

    if audio_file is not None:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        response = transcript["text"]
        st.success("Transcribed: " + response)

    if response:
        st.session_state.responses[question] = response
        st.session_state.step += 1
        st.experimental_rerun()
else:
    st.success("✅ Thank you! Here's a summary of your responses:")
    st.json(st.session_state.responses)
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload a file related to your use case (e.g., screenshot, rubric, student work)", type=["png", "jpg", "jpeg", "pdf"])
    caption = st.text_input("Add a caption or description for the uploaded file")
    if st.button("Submit Use Case"):
        st.success("Your use case has been submitted (this is where database integration would go).")
