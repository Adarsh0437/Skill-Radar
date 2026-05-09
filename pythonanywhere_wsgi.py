import os
import sys


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.environ.setdefault("DB_PATH", os.path.join(PROJECT_DIR, "instance", "skillradar.db"))

from app import app as application
