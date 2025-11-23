import sys
import os
from sqlalchemy import text
from datetime import datetime

# Add src to path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from data_models.database import engine, init_db
from data_models.models import (
    QuestionRaw, VariantGroup, QuestionNormalized, SyllabusNode, 
    TrendSnapshot, PredictionCandidate, SamplePaper, MemoryArtifact,
    ModelRun, EnsembleVote, Exclusion, QuestionParameter, QuestionTopicMap,
    CompositeQuestion, SamplePaperItem, ProvenanceLink, EvaluationResult,
    MemoryType, ExclusionReason, ModelPhase, VoteDecision, CandidateStatus, TopicStatus,
    VECTOR_DIM
)
from sqlmodel import Session, select

def test_all_models():
    print("Initializing database...")
    try:
        # Drop all tables to ensure clean state for new schema
        from sqlmodel import SQLModel
        SQLModel.metadata.drop_all(engine)
        
        init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return

    with Session(engine) as session:
        print("\n--- Testing QuestionRaw ---")
        q_raw = QuestionRaw(
            year=2023,
            raw_text="What is the capital of France?",
            marks=5,
            section="A",
            source_pdf="2023_paper.pdf",
            original_numbering="Q1"
        )
        session.add(q_raw)
        session.commit()
        session.refresh(q_raw)
        print(f"Created QuestionRaw with ID: {q_raw.id}")

        print("\n--- Testing VariantGroup and QuestionNormalized ---")
        v_group = VariantGroup(
            canonical_stem="What is the capital of [Country]?",
            recurrence_count=1,
            signature="sig_123"
        )
        session.add(v_group)
        session.commit()
        session.refresh(v_group)
        print(f"Created VariantGroup with ID: {v_group.id}")

        q_norm = QuestionNormalized(
            base_form="What is the capital of France?",
            marks=5,
            embedding=[0.1] * VECTOR_DIM,
            variant_group_id=v_group.id,
            canonical_hash="hash_123"
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
        parent_node = SyllabusNode(title="Geography", status=TopicStatus.stable)
        session.add(parent_node)
        session.commit()
        session.refresh(parent_node)
        
        child_node = SyllabusNode(title="European Capitals", parent_id=parent_node.id, status=TopicStatus.emerging)
        session.add(child_node)
        session.commit()
        session.refresh(child_node)
        print(f"Created SyllabusNode hierarchy: {parent_node.title} -> {child_node.title}")

        print("\n--- Testing TrendSnapshot ---")
        trend = TrendSnapshot(
            year_range=[2020, 2021, 2022, 2023, 2024],
            topic_stats_json={"Geography": 10},
            emerging_topics=[child_node.id]
        )
        session.add(trend)
        session.commit()
        session.refresh(trend)
        print(f"Created TrendSnapshot with ID: {trend.id}")

        print("\n--- Testing ModelRun ---")
        run = ModelRun(
            phase=ModelPhase.prediction,
            model_name="gpt-4",
            provider="openai"
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        print(f"Created ModelRun with ID: {run.id}")

        print("\n--- Testing PredictionCandidate ---")
        prediction = PredictionCandidate(
            normalized_question_id=q_norm.id,
            trend_snapshot_id=trend.id,
            confidence_scores={"trend": 0.85},
            status=CandidateStatus.pending,
            generated_by_run=run.id
        )
        session.add(prediction)
        session.commit()
        session.refresh(prediction)
        print(f"Created PredictionCandidate with ID: {prediction.id}")

        print("\n--- Testing SamplePaper ---")
        paper = SamplePaper(
            version=1,
            total_marks=100,
            built_by_run=run.id
        )
        session.add(paper)
        session.commit()
        session.refresh(paper)
        print(f"Created SamplePaper with ID: {paper.id}")

        print("\n--- Testing MemoryArtifact ---")
        memory = MemoryArtifact(
            type=MemoryType.semantic,
            content_json={"text": "France is in Europe"},
            embedding=[0.2] * VECTOR_DIM
        )
        session.add(memory)
        session.commit()
        session.refresh(memory)
        print(f"Created MemoryArtifact with ID: {memory.id}")

        print("\nAll models verified successfully!")

if __name__ == "__main__":
    test_all_models()
