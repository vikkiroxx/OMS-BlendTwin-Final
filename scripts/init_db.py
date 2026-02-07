"""
Create BlendTwin config tables if they don't exist.
Run from project root: python scripts/init_db.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from app.database import engine
from app.models import Base

def init():
    Base.metadata.create_all(bind=engine)
    print("Tables created (or already exist).")

if __name__ == "__main__":
    try:
        init()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
