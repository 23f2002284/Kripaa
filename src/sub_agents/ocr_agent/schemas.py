from pydantic import BaseModel, Field
from typing import Optional, List

class PageContent(BaseModel):
    """
    Content of a single page extracted from the PDF.
    """
    page_number: int = Field(..., description="Page number (1-indexed)")
    text: str = Field(..., description="Extracted text content in Markdown")

class ExtractedQuestion(BaseModel):
    """
    A single question extracted from the exam paper.
    """
    original_numbering: str = Field(..., description="Question number (e.g., '1', '2(a)', 'Q1')")
    raw_text: str = Field(..., description="Full text of the question")
    marks: int = Field(..., description="Marks allocated to the question")
    section: Optional[str] = Field(None, description="Section name (e.g., 'Section A')")
    
    # Year might be inferred from context or extracted, but usually passed in metadata
    # If the LLM sees it in the text, it can extract it, otherwise optional.
    year: Optional[int] = Field(None, description="Year if explicitly mentioned in question text")

class ExtractionResult(BaseModel):
    """
    The final structured output from the LLM for a single PDF.
    """
    questions: List[ExtractedQuestion] = Field(..., description="List of extracted questions")

class ExtractedTopic(BaseModel):
    """
    A single topic or unit extracted from the syllabus.
    """
    name: str = Field(..., description="Name of the topic or unit")
    description: Optional[str] = Field(None, description="Description or details of the topic")
    parent_name: Optional[str] = Field(None, description="Name of the parent unit/topic if applicable")
    level: int = Field(..., description="Hierarchy level (1 for Unit, 2 for Chapter, 3 for Topic)")
    estimated_hours: Optional[float] = Field(None, description="Estimated hours if mentioned")

class SyllabusExtractionResult(BaseModel):
    """
    The final structured output from the LLM for a syllabus PDF.
    """
    topics: List[ExtractedTopic] = Field(..., description="List of extracted syllabus topics")