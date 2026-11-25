
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from the project root .env file
load_dotenv()

DATABASE_URL = os.getenv("MEDIFIND_DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "Set MEDIFIND_DATABASE_URL to the MySQL connection URL "
        "before starting MediFind."
    )

engine_options = {"pool_pre_ping": True}

if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {
        "check_same_thread": False
    }

engine = create_engine(
    DATABASE_URL,
    **engine_options
)

Session = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()
