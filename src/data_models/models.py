from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, TEXT
from pgvector.sqlalchemy import Vector

# Constants
VECTOR_DIM = 768

class QuestionRaw(SQLModel, table=True):
    __tablename__ = "question_raw"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    year: int
    text: str = Field(sa_column=Column(TEXT))
    marks: int
    section: Optional[str] = None
    source_pdf: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class VariantGroup(SQLModel, table=True):
    __tablename__ = "variant_group"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    canonical_stem: str = Field(sa_column=Column(TEXT))
    numeric_pattern_signature: Optional[str] = None
    recurrence_count: int = Field(default=0)
    
    questions: List["QuestionNormalized"] = Relationship(back_populates="variant_group")

class QuestionNormalized(SQLModel, table=True):
    __tablename__ = "question_normalized"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    base_form: str = Field(sa_column=Column(TEXT))
    parameter_slots: List[str] = Field(default=[], sa_column=Column(JSONB))
    marks: int
    taxonomy: List[str] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    difficulty_estimate: float = Field(default=0.5)
    
    # Vector embedding for semantic search
    embedding: List[float] = Field(sa_column=Column(Vector(VECTOR_DIM)))
    
    variant_group_id: Optional[UUID] = Field(default=None, foreign_key="variant_group.id")
    variant_group: Optional[VariantGroup] = Relationship(back_populates="questions")

class SyllabusNode(SQLModel, table=True):
    __tablename__ = "syllabus_node"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str
    parent_id: Optional[UUID] = Field(default=None, foreign_key="syllabus_node.id")
    weight: float = Field(default=1.0)
    last_asked_year: Optional[int] = None
    times_asked: int = Field(default=0)
    gap_score: float = Field(default=0.0)
    
    # Self-referential relationship for hierarchy
    # Note: SQLModel requires some workaround for self-referential, 
    # but for simple schema definition this is sufficient.

class TrendSnapshot(SQLModel, table=True):
    __tablename__ = "trend_snapshot"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    year_range: str
    topic_stats: Dict[str, Any] = Field(default={}, sa_column=Column(JSONB))
    recurrence_matrix: List[List[float]] = Field(default=[], sa_column=Column(JSONB))
    emerging_topics: List[str] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    declining_topics: List[str] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PredictionCandidate(SQLModel, table=True):
    __tablename__ = "prediction_candidate"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    normalized_question_id: UUID = Field(foreign_key="question_normalized.id")
    confidence_scores: Dict[str, float] = Field(default={}, sa_column=Column(JSONB)) # {trend, syllabus_gap, ensemble_agreement}
    exclusion_reason: Optional[str] = None
    
class SamplePaper(SQLModel, table=True):
    __tablename__ = "sample_paper"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    version: str
    total_marks: int
    questions: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSONB)) # List of question references/snapshots
    coverage_metrics: Dict[str, float] = Field(default={}, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MemoryArtifact(SQLModel, table=True):
    __tablename__ = "memory_artifact"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    type: str # episodic, semantic, procedural
    content: str = Field(sa_column=Column(TEXT))
    source_refs: List[str] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    lineage: List[str] = Field(default=[], sa_column=Column(JSONB))
    
    # Vector embedding for memory retrieval
    embedding: List[float] = Field(sa_column=Column(Vector(VECTOR_DIM)))
