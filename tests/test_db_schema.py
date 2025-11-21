import sys
import os
from sqlalchemy import text

# Add src to path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from data_models.database import engine, init_db
from data_models.models import QuestionNormalized, MemoryArtifact, VECTOR_DIM
from sqlmodel import Session, select

def test_schema_creation():
    print("Initializing database...")
    try:
        init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return

    print("Verifying tables...")
    with Session(engine) as session:
        # Check if vector extension is enabled
        result = session.exec(text("SELECT * FROM pg_extension WHERE extname = 'vector'")).first()
        if result:
            print("pgvector extension is enabled.")
        else:
            print("WARNING: pgvector extension NOT found.")

        # Create a dummy memory artifact with a vector
        dummy_vector = [0.1] * VECTOR_DIM
        memory = MemoryArtifact(
            type="test",
            content="This is a test memory",
            embedding=dummy_vector
        )
        session.add(memory)
        session.commit()
        session.refresh(memory)
        print(f"Created MemoryArtifact with ID: {memory.id}")

        # Verify we can retrieve it
        statement = select(MemoryArtifact).where(MemoryArtifact.id == memory.id)
        retrieved = session.exec(statement).first()
        if retrieved:
            print("Successfully retrieved MemoryArtifact.")
        else:
            print("Failed to retrieve MemoryArtifact.")

if __name__ == "__main__":
    test_schema_creation()
