from src.data_models.models import (
    # OCR Agent
    QuestionRaw, 

    # Normalization & Canonicalization Agent
    QuestionNormalized, QuestionParameter, CompositeQuestion,

    # Syllabus Mapping & Topic Tagging Agent
    SyllabusNode, QuestionTopicMap, TopicStatus,

    # Memory Management Agent
    MemoryArtifact, MemoryType, VECTOR_DIM,

    # Question generator agent
    # (Models may be shared, e.g. QuestionNormalized)

    # Template Generator Agent
    VariantGroup,

    # Voting & Ranking Agent
    EnsembleVote, VoteDecision,

    # Pattern & Trend Analysis Agent
    TrendSnapshot, PredictionCandidate, CandidateStatus,
    
    # Sample Paper generator agent
    SamplePaper, SamplePaperItem,

    # Reasoning + Report Generation Agent
    ProvenanceLink,

    # Evaluation agent
    ModelRun, EvaluationResult, Exclusion, ExclusionReason, ModelPhase,
    
    # Submission Builder Agent
    # (Uses SamplePaper and others)
)