"""
Central configuration. Reads from .env (free, no paid services required).
"""
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bank_analyzer.db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")

# CORS Configuration for local development and deployed Hugging Face Spaces
raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
CORS_ORIGINS = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]
CORS_ORIGIN_REGEX = os.getenv("CORS_ORIGIN_REGEX", r"^https:\/\/.*\.hf\.space$")

os.makedirs(UPLOAD_DIR, exist_ok=True)
