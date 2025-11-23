from pydantic import BaseModel, Field
from typing import List, Optional

# --- Pydantic Models for Structured Output ---

class QuestionTag(BaseModel):
    """Metadata tags for a single question."""
    question_id: str = Field(description="The UUID of the question being tagged.")
    difficulty: int = Field(description="Difficulty level from 1 (Easy) to 5 (Hard).")
    taxonomy: List[str] = Field(description="Bloom's Taxonomy levels (e.g., 'Recall', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create').")

class TaggingBatchResponse(BaseModel):
    """Response containing tags for a batch of questions."""
    tags: List[QuestionTag]
