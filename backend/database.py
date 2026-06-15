import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Cloud SQL Connection Name (if present, use Cloud Run setup)
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")

# Database credentials (support both Cloud and Local env variables)
DB_USER = os.getenv("DB_USER", os.getenv("POSTGRES_USER", "fpa_user"))
DB_PASSWORD = os.getenv("DB_PASSWORD", os.getenv("POSTGRES_PASSWORD", "fpa_password"))
DB_NAME = os.getenv("DB_NAME", os.getenv("POSTGRES_DB", "fpa_db"))

if CLOUD_SQL_CONNECTION_NAME:
    # Cloud SQL over Unix socket
    SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}?host=/cloudsql/{CLOUD_SQL_CONNECTION_NAME}"
else:
    # Local TCP connection
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
