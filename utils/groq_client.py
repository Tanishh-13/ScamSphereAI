import os

import streamlit as st
from dotenv import load_dotenv
from groq import Groq


load_dotenv()


def get_groq_api_key():

    # -----------------------------------------------------
    # Streamlit Cloud
    # -----------------------------------------------------
    try:
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except st.errors.StreamlitSecretNotFoundError:
        pass

    # -----------------------------------------------------
    # Local development
    # -----------------------------------------------------
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Add GROQ_API_KEY to your local .env file "
            "or Streamlit Cloud Secrets."
        )

    return api_key


client = Groq(
    api_key=get_groq_api_key()
)