"""
Simple web interface for the MarianMT translation project.

Run with:
    pip install streamlit pandas transformers torch sentencepiece sacremoses
    streamlit run translation_app.py
"""

import io
import pandas as pd
import streamlit as st
from transformers import MarianMTModel, MarianTokenizer

# ---------------------------------------------------------------------------
# Supported language pairs (same models as the original script)
# ---------------------------------------------------------------------------
LANGUAGE_PAIRS = {
    "English -> French": "Helsinki-NLP/opus-mt-en-fr",
    "English -> German": "Helsinki-NLP/opus-mt-en-de",
    "English -> Spanish": "Helsinki-NLP/opus-mt-en-es",
    "English -> Chinese": "Helsinki-NLP/opus-mt-en-zh",
    "English -> Japanese": "Helsinki-NLP/opus-mt-en-ja",
    "English -> Italian": "Helsinki-NLP/opus-mt-en-it",
    "English -> Russian": "Helsinki-NLP/opus-mt-en-ru",
    "English -> Portuguese": "Helsinki-NLP/opus-mt-en-pt",
    "English -> Dutch": "Helsinki-NLP/opus-mt-en-nl",
    "English -> Hindi": "Helsinki-NLP/opus-mt-en-hi",
    "English -> Arabic": "Helsinki-NLP/opus-mt-en-ar",
}


# ---------------------------------------------------------------------------
# Model loading (cached so each model is only downloaded/loaded once)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_model(model_name: str):
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)
    return tokenizer, model


def translate_texts(texts, model_name: str):
    tokenizer, model = load_model(model_name)
    translated = []
    for text in texts:
        inputs = tokenizer([text], return_tensors="pt", padding=True, truncation=True)
        outputs = model.generate(**inputs)
        translated.append(tokenizer.decode(outputs[0], skip_special_tokens=True))
    return translated


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Text Translator", page_icon="🌐", layout="centered")
st.title("🌐 Text Translator")
st.caption("Powered by Helsinki-NLP MarianMT models via Hugging Face Transformers")

pair_label = st.selectbox("Target language", list(LANGUAGE_PAIRS.keys()))
model_name = LANGUAGE_PAIRS[pair_label]

tab_text, tab_file = st.tabs(["✍️ Translate text", "📄 Translate a CSV"])

# ---- Single text input -----------------------------------------------------
with tab_text:
    source_text = st.text_area(
        "Enter text to translate",
        height=150,
        placeholder="Type or paste English text here...",
    )

    if st.button("Translate", type="primary", key="translate_text_btn"):
        if not source_text.strip():
            st.warning("Please enter some text first.")
        else:
            with st.spinner(f"Translating ({pair_label})..."):
                result = translate_texts([source_text], model_name)[0]
            st.subheader("Translated text")
            st.text_area("Output", value=result, height=150, key="translated_output")

# ---- Batch CSV input --------------------------------------------------------
with tab_file:
    st.write("Upload a CSV with a `reviewText` column to translate every row.")
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if "reviewText" not in df.columns:
            st.error("The uploaded CSV does not contain a 'reviewText' column.")
        else:
            st.write(f"Loaded {len(df)} rows.")
            if st.button("Translate CSV", type="primary", key="translate_csv_btn"):
                with st.spinner(f"Translating {len(df)} rows ({pair_label})..."):
                    df["translated_text"] = translate_texts(df["reviewText"].tolist(), model_name)
                st.success("Done!")
                st.dataframe(df[["reviewText", "translated_text"]])

                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                st.download_button(
                    "Download translated_reviews.csv",
                    data=csv_buffer.getvalue(),
                    file_name="translated_reviews.csv",
                    mime="text/csv",
                )
