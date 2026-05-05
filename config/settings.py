import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-04-17")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")