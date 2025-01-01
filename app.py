from io import BytesIO
import re
import time

import streamlit as st
from audiorecorder import audiorecorder
from dotenv import dotenv_values
from openai import OpenAI
from pydub import AudioSegment

env = dotenv_values(".env")
AUDIO_TRANSCRIBE_MODEL = "whisper-1"

def get_openai_client():
    return OpenAI(api_key=st.session_state["openai_api_key"])


# def transcribe_audio_to_text(audio_path):
#     openai_client = get_openai_client()
#     with open(audio_path, "rb") as f:
#         transcript = openai_client.audio.transcriptions.create(
#             file=f,
#             model="whisper-1",
#             response_format="verbose_json",
#         )

#     return transcript.text


def transcribe_audio(audio_bytes):
    openai_client = get_openai_client()
    audio_file = BytesIO(audio_bytes)
    audio_file.name = "audio.mp3"
    transcript = openai_client.audio.transcriptions.create(
        file=audio_file,
        model=AUDIO_TRANSCRIBE_MODEL,
        response_format="verbose_json",
        timestamp_granularities=["word", "segment"],
    )

    return {
        "text": transcript.text,
        "words": transcript.words,
    }

#
# MAIN
#
st.set_page_config(page_title="Wycinanie fragmentów audio", layout="centered")

# OpenAI API key protection
if not st.session_state.get("openai_api_key"):
    if "OPENAI_API_KEY" in env:
        st.session_state["openai_api_key"] = env["OPENAI_API_KEY"]
    else:
        st.info("Dodaj swój klucz API OpenAI aby móc korzystać z tej aplikacji")
        st.session_state["openai_api_key"] = st.text_input("Klucz API", type="password")
        if st.session_state["openai_api_key"]:
            st.rerun()
if not st.session_state.get("openai_api_key"):
    st.stop()

st.session_state.setdefault("new_audio_bytes", None)
st.session_state.setdefault("new_audio_text", "")
st.session_state.setdefault("transcription", "")

st.title("Wycinanie fragmentów audio")

new_audio = audiorecorder(
    start_prompt="Nagraj audio",
    stop_prompt="Zatrzymaj nagrywanie",
)

transcription = {
    "text": "",
    "words": [],
}

if new_audio:
    audio = BytesIO()
    new_audio.export(audio, format="mp3")
    st.session_state["new_audio_bytes"] = audio.getvalue()
    st.audio(audio, format="audio/mp3")
    transcription = transcribe_audio(st.session_state["new_audio_bytes"])
    # if transcription != st.session_state["new_audio_text"]:
    #     st.session_state["new_audio_text"] = st.session_state["transcription"]

new_text = st.text_area(
    "Transkrypcja (zaznacz fragment, który chcesz usunąć z audio)", 
    value=transcription['text'],
)
text_with_edits = new_text
if st.button("Zapisz zmiany"):
    # st.text(new_text)
    # marked_words = re.findall(r'\[\[(.*?)\]\]', new_text)
    # for word in marked_words:
    #    st.text(word)
    


    words = new_text.split()
    rem_starts = []
    rem_ends = []
    
    for idx, word in enumerate(words):
        if word.startswith("[["):
            rem_starts.append(transcription['words'][idx]['start'])
        if word.endswith("]]"):
            rem_ends.append(transcription['words'][idx]['end'])

    
    temp_audio = AudioSegment.from_file(audio)
    output_audio = AudioSegment.empty()
    for start, end in zip(rem_starts, rem_ends):
        print(start, end)
        output_audio += temp_audio[start:end]
    output_audio.export("output.mp3", format="mp3")

    st.audio("output.mp3", format="audio/mp3")

    
