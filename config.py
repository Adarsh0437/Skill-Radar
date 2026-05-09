import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "skillradar-dev-secret")
    DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
    DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "instance", "skillradar.db"))
