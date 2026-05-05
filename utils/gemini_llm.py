"""Gemini LLM wrapper for Dify DSL Generator"""

import os
import google.generativeai as genai
from config.settings import Settings


def get_gemini_client():
    """Initialize and return a Gemini GenerativeModel client."""
    genai.configure(api_key=Settings.GEMINI_API_KEY)
    return genai.GenerativeModel(model_name=Settings.GEMINI_MODEL)
