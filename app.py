# GenAI Use Case Collection Chatbot (Prototype)
# Streamlit + OpenAI GPT + Whisper + Image Upload

import streamlit as st
import openai
import os
from PIL import Image

# --- Config ---
openai.api_key = os.getenv("OPENAI_API_KEY")  # Add this in Streamlit secrets

# --- Title ---
st.title("🧠 GenAI Use Case Collection Chatbot")
st.write("Chat with this assistant to share how you're using GenAI in teaching and assessment.")

# --- Option for Input Mode ---
mode = st.radio("Choose your response mode:", ["Type", "Speak"])

# --- Chatbot Questions ---
def get_questions():
    return [
        "What GenAI tool(s) did you use?",
        "How did you use it in your teaching or assessment?",
        "What were your goals or intended outcomes?",
        "What was the observed impact?",
        "What challenges or concerns did you face?",
        "What would you do differently next time?",
        "Do you have any advice for others wanting to try this?"
    ]

# --- Chat Interaction ---
def collect_text_responses():
    responses = {}
    questions = get_questions()
    for q in questions:
        responses[q] = st.text_area(q)
    return responses

# --- Voice Interaction (uses Whisper) ---
def collect_voice_responses():
    responses = {}
    questions = get_questions()
    for q in questions:
        st.write(f"🎙️ {q}")
        audio_file = st.file_uploader("Upload your audio response (MP3 or WAV)", type=["mp3", "wav"], key=q)
        if audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            responses[q] = transcript["text"]
            st.success("Transcribed: " + transcript["text"])
    return responses

# --- Image Upload ---
st.markdown("### 📎 Upload a screenshot or file (optional)")
uploaded_image = st.file_uploader("Upload a file related to your use case (e.g., screenshot, rubric, student work)", type=["png", "jpg", "jpeg", "pdf"])
image_caption = st.text_input("Add a caption or description for the uploaded file")

# --- Run Collection ---
st.markdown("---")
st.markdown("### 💬 Submit Your Use Case")
if mode == "Type":
    data = collect_text_responses()
else:
    data = collect_voice_responses()

# --- Submission ---
if st.button("Submit Use Case"):
    st.success("✅ Thank you! Your GenAI use case has been recorded.")
    st.json({
        "responses": data,
        "uploaded_file": uploaded_image.name if uploaded_image else None,
        "caption": image_caption
    })
