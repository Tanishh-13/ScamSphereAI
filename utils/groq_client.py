import os
import streamlit as st
from groq import Groq


def get_groq_api_key():
    # Streamlit Cloud / Streamlit secrets
    if "GROQ_API_KEY" in st.secrets:
        return st.secrets["GROQ_API_KEY"]

    # Local development fallback
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Add it to Streamlit Secrets or your local .env file."
        )

    return api_key


client = Groq(
    api_key=get_groq_api_key()
)