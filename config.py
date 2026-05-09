import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "skillradar-dev-secret")
    DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
    DB_PATH = os.getenv("DB_PATH", "instance/skillradar.db")
