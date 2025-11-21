from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
import os

# Default to a local postgres instance if not provided
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/kripaa_db")

engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    """
    Initializes the database.
    Ensures the vector extension exists and creates all tables.
    """
    with Session(engine) as session:
        # Enable pgvector extension
        session.exec(text("CREATE EXTENSION IF NOT EXISTS vector"))
        session.commit()
    
    # Create tables
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
