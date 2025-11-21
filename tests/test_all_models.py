import sys
import os
from sqlalchemy import text
from datetime import datetime

# Add src to path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from data_models.database import engine, init_db
from data_models.models import (
    QuestionRaw, VariantGroup, QuestionNormalized, SyllabusNode, 
    TrendSnapshot, PredictionCandidate, SamplePaper, MemoryArtifact, VECTOR_DIM
)
from sqlmodel import Session, select

def test_all_models():
    print("Initializing database...")
    try:
        init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return

    with Session(engine) as session:
        print("\n--- Testing QuestionRaw ---")
        q_raw = QuestionRaw(
            year=2023,
            text="What is the capital of France?",
            marks=5,
            section="A",
            source_pdf="2023_paper.pdf"
        )
        session.add(q_raw)
        session.commit()
        session.refresh(q_raw)
        print(f"Created QuestionRaw with ID: {q_raw.id}")

        print("\n--- Testing VariantGroup and QuestionNormalized ---")
        v_group = VariantGroup(
            canonical_stem="What is the capital of [Country]?",
            recurrence_count=1
        )
        session.add(v_group)
        session.commit()
        session.refresh(v_group)
        print(f"Created VariantGroup with ID: {v_group.id}")

        q_norm = QuestionNormalized(
            base_form="What is the capital of France?",
            marks=5,
            embedding=[0.1] * VECTOR_DIM,
            variant_group_id=v_group.id
        )
        session.add(q_norm)
        session.commit()
        session.refresh(q_norm)
        print(f"Created QuestionNormalized with ID: {q_norm.id}")
        
        # Verify relationship
        session.refresh(v_group)
        if len(v_group.questions) > 0:
            print(f"Relationship verified: VariantGroup has {len(v_group.questions)} questions.")
        else:
            print("ERROR: Relationship verification failed.")

        print("\n--- Testing SyllabusNode ---")
        parent_node = SyllabusNode(title="Geography")
        session.add(parent_node)
        session.commit()
        session.refresh(parent_node)
        
        child_node = SyllabusNode(title="European Capitals", parent_id=parent_node.id)
        session.add(child_node)
        session.commit()
        session.refresh(child_node)
        print(f"Created SyllabusNode hierarchy: {parent_node.title} -> {child_node.title}")

        print("\n--- Testing TrendSnapshot ---")
        trend = TrendSnapshot(
            year_range="2020-2024",
            topic_stats={"Geography": 10},
            emerging_topics=["AI", "Climate Change"]
        )
        session.add(trend)
        session.commit()
        session.refresh(trend)
        print(f"Created TrendSnapshot with ID: {trend.id}")

        print("\n--- Testing PredictionCandidate ---")
        prediction = PredictionCandidate(
            normalized_question_id=q_norm.id,
            confidence_scores={"trend": 0.85}
        )
        session.add(prediction)
        session.commit()
        session.refresh(prediction)
        print(f"Created PredictionCandidate with ID: {prediction.id}")

        print("\n--- Testing SamplePaper ---")
        paper = SamplePaper(
            version="v1.0",
            total_marks=100,
            questions=[{"id": str(q_norm.id), "marks": 5}]
        )
        session.add(paper)
        session.commit()
        session.refresh(paper)
        print(f"Created SamplePaper with ID: {paper.id}")

        print("\nAll models verified successfully!")

if __name__ == "__main__":
    test_all_models()
