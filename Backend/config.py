import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent / ".env")


class Config:
    """Application settings kept ready for environment-based configuration."""

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "24"))
    )

    CORS_ORIGINS = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    )
