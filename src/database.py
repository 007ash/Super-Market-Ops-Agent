import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ExpectingDATABASE_URL, fallback for local dev
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ai_smart_mart")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
