from typing import TypedDict, List
from uuid import UUID

class PipelineState(TypedDict):
    """State for the exam generation pipeline."""
    target_year: int
    pyq_directory: str
    syllabus_directory: str
    
    # Intermediate data
    snapshot_id: UUID | None
    paper_markdown: str | None
    
    # Status
    current_step: str
    errors: List[str]
    completed: bool