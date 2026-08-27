import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME")
APP_VERSION = os.getenv("APP_VERSION")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")