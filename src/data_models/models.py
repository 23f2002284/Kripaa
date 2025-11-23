from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, TEXT
from pgvector.sqlalchemy import Vector

# Constants
VECTOR_DIM = 768

# Enums
class MemoryType(str, Enum):
    episodic = "episodic"
    semantic = "semantic"
    procedural = "procedural"
    working = "working"

class ExclusionReason(str, Enum):
    redundant_variant = "redundant_variant"
    overrepresented_topic = "overrepresented_topic"
    low_confidence_trend = "low_confidence_trend"
    outlier_difficulty = "outlier_difficulty"
    syllabus_mismatch = "syllabus_mismatch"
    insufficient_recurrence = "insufficient_recurrence"
    composite_superseded = "composite_superseded"

class ModelPhase(str, Enum):
    ocr = "ocr"
    normalization = "normalization"
    mapping = "mapping"
    trend = "trend"
    prediction = "prediction"
    ensemble = "ensemble"
    report = "report"
    evaluation = "evaluation"

class VoteDecision(str, Enum):
    include = "include"
    exclude = "exclude"

class CandidateStatus(str, Enum):
    pending = "pending"
    selected = "selected"
    excluded = "excluded"

class TopicStatus(str, Enum):
    emerging = "emerging"
    declining = "declining"
    stable = "stable"

# Models

class QuestionRaw(SQLModel, table=True):
    __tablename__ = "questions_raw"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    year: int = Field(index=True)
    section: Optional[str] = None
    original_numbering: Optional[str] = None
    raw_text: str = Field(sa_column=Column(TEXT))
    marks: Optional[int] = None
    source_pdf: Optional[str] = None
    ocr_confidence: Optional[float] = None
    processed: bool = Field(default=False)
    ingestion_time: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class VariantGroup(SQLModel, table=True):
    __tablename__ = "variant_groups"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    canonical_stem: str = Field(sa_column=Column(TEXT))
    slot_count: int = Field(default=0)
    recurrence_count: int = Field(default=0)
    first_year: Optional[int] = None
    last_year: Optional[int] = None
    signature: Optional[str] = Field(default=None, sa_column=Column(TEXT, unique=True))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Vector embedding for the canonical stem
    embedding: List[float] = Field(sa_column=Column(Vector(VECTOR_DIM)))
    
    syllabus_node_id: Optional[UUID] = Field(default=None, foreign_key="syllabus_nodes.id")
    syllabus_node: Optional["SyllabusNode"] = Relationship(back_populates=None) # One-way relationship is fine for now
    
    questions: List["QuestionNormalized"] = Relationship(back_populates="variant_group")

class QuestionNormalized(SQLModel, table=True):
    __tablename__ = "questions_normalized"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    base_form: str = Field(sa_column=Column(TEXT))
    marks: Optional[int] = None
    difficulty: Optional[int] = None # 1-5
    variant_group_id: Optional[UUID] = Field(default=None, foreign_key="variant_groups.id")
    canonical_hash: str = Field(sa_column=Column(TEXT))
    original_ids: List[UUID] = Field(default=[], sa_column=Column(ARRAY(TEXT))) # Storing UUIDs as strings in array for simplicity or UUID array
    placeholders: List[str] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    taxonomy: List[str] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Vector embedding (not in SQL schema explicitly but needed for functionality)
    embedding: List[float] = Field(sa_column=Column(Vector(VECTOR_DIM)))
    
    variant_group: Optional[VariantGroup] = Relationship(back_populates="questions")
    parameters: List["QuestionParameter"] = Relationship(back_populates="question")
    topic_maps: List["QuestionTopicMap"] = Relationship(back_populates="question")
    prediction_candidates: List["PredictionCandidate"] = Relationship(back_populates="normalized_question")

class QuestionParameter(SQLModel, table=True):
    __tablename__ = "question_parameters"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    question_id: UUID = Field(foreign_key="questions_normalized.id")
    placeholder: str
    param_type: Optional[str] = None
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    notes: Optional[str] = None
    
    question: QuestionNormalized = Relationship(back_populates="parameters")

class SyllabusNode(SQLModel, table=True):
    __tablename__ = "syllabus_nodes"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    topic: str
    description: Optional[str] = Field(sa_column=Column(TEXT))
    module: str
    parent_topic: Optional[str] = None # The 'title' or chapter name
    level: int = Field(default=3) # 1=Unit, 2=Chapter, 3=Topic. Mostly 3 now.
    estimated_hours: float = Field(default=0.0)
    code: Optional[str] = None
    weight: float = Field(default=1.0)
    times_asked: int = Field(default=0)
    last_asked_year: Optional[int] = None
    gap_score: float = Field(default=0.0)
    status: TopicStatus = Field(default=TopicStatus.stable)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Vector embedding
    embedding: List[float] = Field(sa_column=Column(Vector(VECTOR_DIM)))
    
    topic_maps: List["QuestionTopicMap"] = Relationship(back_populates="topic")

class QuestionTopicMap(SQLModel, table=True):
    __tablename__ = "question_topic_map"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    question_id: UUID = Field(foreign_key="questions_normalized.id")
    topic_id: UUID = Field(foreign_key="syllabus_nodes.id")
    relevance_score: float = Field(default=1.0)
    source: Optional[str] = None
    
    question: QuestionNormalized = Relationship(back_populates="topic_maps")
    topic: SyllabusNode = Relationship(back_populates="topic_maps")

class CompositeQuestion(SQLModel, table=True):
    __tablename__ = "composite_questions"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: Optional[str] = None
    parts: List[UUID] = Field(default=[], sa_column=Column(ARRAY(TEXT))) # References questions_normalized ids
    constructed_stem: Optional[str] = Field(sa_column=Column(TEXT))
    marks: Optional[int] = None
    rationale: Optional[str] = Field(sa_column=Column(TEXT))
    source_variant_group_id: Optional[UUID] = Field(default=None, foreign_key="variant_groups.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TrendSnapshot(SQLModel, table=True):
    __tablename__ = "trend_snapshots"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    year_range: List[int] = Field(sa_column=Column(ARRAY(JSONB))) # Using JSONB for int array compatibility if needed, or ARRAY(Integer)
    topic_stats_json: Dict[str, Any] = Field(default={}, sa_column=Column(JSONB))
    emerging_topics: List[UUID] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    declining_topics: List[UUID] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    prediction_candidates: List["PredictionCandidate"] = Relationship(back_populates="trend_snapshot")

class ModelRun(SQLModel, table=True):
    __tablename__ = "model_runs"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    phase: ModelPhase
    model_name: str
    model_version: Optional[str] = None
    provider: Optional[str] = None
    temperature: Optional[float] = None
    seed: Optional[int] = None
    input_ref: Optional[UUID] = None
    output_ref: Optional[UUID] = None
    parameters_json: Dict[str, Any] = Field(default={}, sa_column=Column(JSONB))
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class PredictionCandidate(SQLModel, table=True):
    __tablename__ = "prediction_candidates"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    normalized_question_id: UUID = Field(foreign_key="questions_normalized.id")
    trend_snapshot_id: Optional[UUID] = Field(default=None, foreign_key="trend_snapshots.id")
    scores_json: Dict[str, float] = Field(default={}, sa_column=Column(JSONB))
    status: CandidateStatus = Field(default=CandidateStatus.pending)
    generated_by_run: Optional[UUID] = Field(default=None, foreign_key="model_runs.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    normalized_question: QuestionNormalized = Relationship(back_populates="prediction_candidates")
    trend_snapshot: Optional[TrendSnapshot] = Relationship(back_populates="prediction_candidates")
    ensemble_votes: List["EnsembleVote"] = Relationship(back_populates="candidate")
    exclusions: List["Exclusion"] = Relationship(back_populates="candidate")

class EnsembleVote(SQLModel, table=True):
    __tablename__ = "ensemble_votes"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    candidate_id: UUID = Field(foreign_key="prediction_candidates.id")
    model_run_id: UUID = Field(foreign_key="model_runs.id")
    decision: VoteDecision
    confidence: Optional[float] = None
    rationale: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    candidate: PredictionCandidate = Relationship(back_populates="ensemble_votes")

class Exclusion(SQLModel, table=True):
    __tablename__ = "exclusions"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    candidate_id: UUID = Field(foreign_key="prediction_candidates.id")
    reason: ExclusionReason
    rationale: Optional[str] = None
    model_run_id: Optional[UUID] = Field(default=None, foreign_key="model_runs.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    candidate: PredictionCandidate = Relationship(back_populates="exclusions")

class SamplePaper(SQLModel, table=True):
    __tablename__ = "sample_papers"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    version: int = Field(unique=True)
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_marks: Optional[int] = None
    coverage_metrics_json: Dict[str, float] = Field(default={}, sa_column=Column(JSONB))
    built_by_run: Optional[UUID] = Field(default=None, foreign_key="model_runs.id")
    locked: bool = Field(default=True)
    
    items: List["SamplePaperItem"] = Relationship(back_populates="paper")

class SamplePaperItem(SQLModel, table=True):
    __tablename__ = "sample_paper_items"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    paper_id: UUID = Field(foreign_key="sample_papers.id")
    candidate_id: Optional[UUID] = Field(default=None, foreign_key="prediction_candidates.id")
    composite_question_id: Optional[UUID] = Field(default=None, foreign_key="composite_questions.id")
    ordering: int
    marks: Optional[int] = None
    origin_type: Optional[str] = None
    source_year: Optional[int] = None
    notes: Optional[str] = None
    
    paper: SamplePaper = Relationship(back_populates="items")

class MemoryArtifact(SQLModel, table=True):
    __tablename__ = "memory_artifacts"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    type: MemoryType
    title: Optional[str] = None
    content_json: Dict[str, Any] = Field(sa_column=Column(JSONB))
    source_refs: List[UUID] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    lineage: List[UUID] = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    hash: Optional[str] = None
    version: int = Field(default=1)
    
    # Vector embedding
    embedding: List[float] = Field(sa_column=Column(Vector(VECTOR_DIM)))

class ProvenanceLink(SQLModel, table=True):
    __tablename__ = "provenance_links"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source_id: UUID
    target_id: UUID
    relation: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EvaluationResult(SQLModel, table=True):
    __tablename__ = "evaluation_results"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    model_run_id: Optional[UUID] = Field(default=None, foreign_key="model_runs.id")
    context_years: List[int] = Field(sa_column=Column(ARRAY(JSONB))) # or ARRAY(Integer)
    target_year: Optional[int] = None
    metrics_json: Dict[str, Any] = Field(sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)
