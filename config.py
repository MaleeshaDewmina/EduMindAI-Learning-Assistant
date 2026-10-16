import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()


class Config:
    # A strong SECRET_KEY must be set in the local, never-committed .env file.
    SECRET_KEY = os.getenv("SECRET_KEY")

    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD", ""))
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "edumind_ai_db")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    # Groq retired llama-3.1-8b-instant for developer/free accounts in August 2026.
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Enable only after deploying behind HTTPS (localhost development uses HTTP).
    SESSION_COOKIE_SECURE = os.getenv("HTTPS_ENABLED", "false").lower() == "true"
    MAX_CONTENT_LENGTH = 1024 * 1024  # Reject requests larger than 1 MiB.
