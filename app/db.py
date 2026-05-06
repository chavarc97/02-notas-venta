import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# We expect DATABASE_URL in the .env file, e.g., postgresql://user:password@localhost:5432/dbname
DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite:///./test.db"
)  # Fallback to sqlite for local dev if not provided

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
