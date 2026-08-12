from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUNTIME_DIR = os.path.join(BASE_DIR, ".local")
LEGACY_DATABASE_PATH = os.path.join(BASE_DIR, "customer_manager.db")
DATABASE_FILE_PATH = os.getenv("CUSTOMER_MANAGER_DB_PATH", os.path.join(RUNTIME_DIR, "customer_manager.db"))


def ensure_runtime_storage():
    os.makedirs(os.path.dirname(DATABASE_FILE_PATH), exist_ok=True)

    if DATABASE_FILE_PATH != LEGACY_DATABASE_PATH and not os.path.exists(DATABASE_FILE_PATH) and os.path.exists(LEGACY_DATABASE_PATH):
        shutil.copy2(LEGACY_DATABASE_PATH, DATABASE_FILE_PATH)


ensure_runtime_storage()
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_FILE_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()