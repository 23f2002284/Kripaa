"""Deduplication utility for candidate questions."""
import numpy as np
from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from utils.logger import get_logger
from utils.llm import generate_embedding
from src.data_models.models import PredictionCandidate, CandidateStatus, QuestionNormalized

logger = get_logger()

def normalize_text(text: str) -> str:
    """
    Basic text normalization.
    - Trims whitespace
    - Standardizes line breaks
    """
    if not text:
        return ""
    return text.strip()

async def deduplicate_candidates(
    candidates: List[PredictionCandidate],
    snapshot_id: UUID,
    session,
    similarity_threshold: float = 0.92
) -> List[PredictionCandidate]:
    """
    Remove duplicate candidates by comparing embeddings with already-selected questions.
    Uses a hybrid strategy:
    1. Exact String Match (on normalized text)
    2. Vector Similarity Match (Cosine Similarity)
    
    Args:
        candidates: List of newly generated candidates to deduplicate
        snapshot_id: Snapshot ID to fetch already-selected questions from
        session: Database session
        similarity_threshold: Cosine similarity threshold above which questions are considered duplicates
    
    Returns:
        Filtered list of candidates with duplicates removed
    """
    logger.info(f"Deduplicating {len(candidates)} candidates (threshold: {similarity_threshold})...")
    
    # Fetch already-selected candidates with their questions
    stmt_selected = select(PredictionCandidate).where(
        PredictionCandidate.trend_snapshot_id == snapshot_id,
        PredictionCandidate.status == CandidateStatus.selected
    ).options(selectinload(PredictionCandidate.normalized_question))
    
    result_selected = await session.execute(stmt_selected)
    selected_candidates = result_selected.scalars().all()
    
    # Build list of selected question embeddings and texts
    selected_data = []
    for candidate in selected_candidates:
        if candidate.normalized_question:
            norm_text = normalize_text(candidate.normalized_question.base_form)
            
            # Ensure embedding exists
            if candidate.normalized_question.embedding:
                emb_array = np.array(candidate.normalized_question.embedding)
                selected_data.append((norm_text, emb_array))
    
    if len(selected_data) == 0:
        logger.info("No previously selected questions to compare against, skipping deduplication")
        return candidates
    
    logger.info(f"Comparing against {len(selected_data)} already-selected questions")
    
    # Ensure all newly generated candidates have embeddings
    for candidate in candidates:
        if not candidate.normalized_question:
            continue
            
        # Generate embedding if missing
        if not candidate.normalized_question.embedding or len(candidate.normalized_question.embedding) == 0:
            try:
                norm_text = normalize_text(candidate.normalized_question.base_form)
                embedding = await generate_embedding(norm_text)
                candidate.normalized_question.embedding = embedding
            except Exception as e:
                logger.warning(f"Failed to generate embedding for candidate: {e}")
    
    # Apply deduplication
    filtered_candidates = []
    duplicates_removed = 0
    
    for candidate in candidates:
        if not candidate.normalized_question:
            filtered_candidates.append(candidate)
            continue
            
        candidate_text = normalize_text(candidate.normalized_question.base_form)
        
        # 1. Exact String Match Check
        is_exact_duplicate = False
        for selected_text, _ in selected_data:
            if candidate_text == selected_text:
                logger.info(f"Exact duplicate detected: {candidate_text[:50]}...")
                is_exact_duplicate = True
                duplicates_removed += 1
                break
        
        if is_exact_duplicate:
            continue

        # 2. Vector Similarity Check
        if not candidate.normalized_question.embedding:
            # Keep candidates without embeddings if they passed string check
            filtered_candidates.append(candidate)
            continue
            
        candidate_embedding = np.array(candidate.normalized_question.embedding)
        is_vector_duplicate = False
        
        for selected_text, selected_embedding in selected_data:
            # Compute cosine similarity
            similarity = np.dot(candidate_embedding, selected_embedding) / (
                np.linalg.norm(candidate_embedding) * np.linalg.norm(selected_embedding)
            )
            
            if similarity >= similarity_threshold:
                logger.info(f"Vector duplicate detected (similarity: {similarity:.3f})")
                logger.info(f"  New: {candidate_text[:60]}...")
                logger.info(f"  Existing: {selected_text[:60]}...")
                is_vector_duplicate = True
                duplicates_removed += 1
                break
        
        if not is_vector_duplicate:
            filtered_candidates.append(candidate)
    
    logger.info(f"Deduplication complete: {duplicates_removed} duplicates removed, {len(filtered_candidates)} candidates remaining")
    return filtered_candidates
