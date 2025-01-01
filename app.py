from io import BytesIO

import streamlit as st
from audiorecorder import audiorecorder
from dotenv import dotenv_values
from openai import OpenAI
from pydub import AudioSegment

env = dotenv_values(".env")
AUDIO_TRANSCRIBE_MODEL = "whisper-1"

def get_openai_client():
    return OpenAI(api_key=st.session_state["openai_api_key"])

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

new_text = ""
if new_audio:
   
    new_text = st.text_area(
        "",  value=transcription['text'])
    st.markdown(
        "Zaznacz w powyższym tekście fragmenty, który chcesz usunąć z audio, " 
        "otaczając je podwójnymi nawiasami kwadratowymi np. [[to jest fragment do usunięcia]]")

if new_text:
    text_with_edits = new_text
    if st.button("Wytnij zaznaczone fragmenty"):
        words = new_text.split(' ')
        rem_starts = []
        rem_ends = []
        
        for idx, word in enumerate(words):
            _start = transcription['words'][idx]['start']*1000
            _end = transcription['words'][idx]['end']*1000
            _med = (_start + _end) / 2
            if '[[' in word:
                if word.find('[[') < len(word)/3:
                    rem_starts.append(_start)
                elif word.find('[[') > len(word)*2/3:
                    rem_starts.append(_end)
                else:
                    rem_starts.append(_med)
                
            if ']]' in word:
                if word.find(']]') < len(word)/3:
                    rem_ends.append(_start)
                elif word.find(']]') > len(word)*2/3:
                    rem_ends.append(_end)
                else:
                    rem_ends.append(_med)

        
        temp_audio = AudioSegment.from_file(audio)
        output_audio = AudioSegment.empty()
        last_end = 0
        for start, end in zip(rem_starts, rem_ends):
            output_audio += temp_audio[last_end:start]
            last_end = end
        output_audio += temp_audio[last_end:]
        
        output_audio_bytes = BytesIO()
        output_audio.export(output_audio_bytes, format="mp3")

        st.audio(output_audio_bytes, format="audio/mp3")
        st.download_button(
            label="Pobierz audio", data=output_audio_bytes, 
            file_name="output.mp3", mime="audio/mp3")

    
