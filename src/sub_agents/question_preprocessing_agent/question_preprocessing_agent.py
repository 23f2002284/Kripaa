import asyncio
import hashlib
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector

from utils.db import get_session
from utils.logger import get_logger
from utils.llm import generate_embedding
from src.data_models.models import QuestionRaw, QuestionNormalized, VariantGroup

logger = get_logger()

# Thresholds
SIMILARITY_THRESHOLD = 0.95

def normalize_text(text: str) -> str:
    """
    Basic text normalization.
    - Trims whitespace
    - Standardizes line breaks (optional, but keeping markdown structure is key)
    """
    if not text:
        return ""
    return text.strip()

def get_canonical_hash(text: str) -> str:
    """
    Generate a deterministic hash for the normalized text.
    Using SHA256.
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

async def find_duplicate(session: AsyncSession, text: str, embedding: List[float]) -> Optional[QuestionNormalized]:
    """
    Finds a duplicate question using Hybrid Strategy:
    1. Exact String Match (on normalized text)
    2. Vector Similarity Match (> 0.95)
    """
    # 1. Exact String Match
    stmt = select(QuestionNormalized).where(QuestionNormalized.base_form == text).limit(1)
    result = await session.execute(stmt)
    exact_match = result.scalar_one_or_none()
    if exact_match:
        logger.info(f"Found exact string duplicate: {exact_match.id}")
        return exact_match

    # 2. Vector Similarity Match
    # Using pgvector's cosine distance operator (<=>). 
    # 1 - distance = similarity. So distance < (1 - threshold).
    # threshold 0.95 => distance < 0.05
    distance_threshold = 1 - SIMILARITY_THRESHOLD
    
    # We select the closest match
    dist_expr = QuestionNormalized.embedding.cosine_distance(embedding)
    stmt = select(QuestionNormalized, dist_expr).order_by(dist_expr).limit(1)
    
    result = await session.execute(stmt)
    match_row = result.first()
    
    if match_row:
        match, distance = match_row
        # Ensure distance is within threshold
        if distance < distance_threshold:
            logger.info(f"Found vector duplicate: {match.id} (Distance: {distance:.4f})")
            return match

    return None

async def process_questions():
    """
    Main loop to process pending raw questions.
    """
    logger.info("Starting Question Preprocessing...")
    
    async for session in get_session():
        try:
            # 1. Fetch Raw Questions that haven't been processed
            stmt = select(QuestionRaw).where(QuestionRaw.processed == False)
            result = await session.execute(stmt)
            raw_questions = result.scalars().all()
            
            logger.info(f"Found {len(raw_questions)} pending raw questions.")
            
            processed_count = 0
            
            for raw_q in raw_questions:
                normalized_text = normalize_text(raw_q.raw_text)
                if not normalized_text:
                    # Mark as processed even if empty to avoid stuck loop? 
                    # Or maybe just skip. Let's mark as processed but warn.
                    logger.warning(f"Empty text for Raw Q {raw_q.id}. Marking as processed.")
                    raw_q.processed = True
                    raw_q.updated_at = datetime.utcnow()
                    session.add(raw_q)
                    continue
                
                # Generate Embedding
                try:
                    embedding = await generate_embedding(normalized_text)
                except Exception as e:
                    logger.error(f"Failed to generate embedding for Q {raw_q.id}: {e}")
                    # Do NOT mark as processed so we retry later? 
                    # Or mark as failed? For now, skip and retry next run.
                    continue
                
                # Deduplicate
                duplicate = await find_duplicate(session, normalized_text, embedding)
                
                if duplicate:
                    # Link this raw question to the existing normalized question
                    if str(raw_q.id) not in duplicate.original_ids:
                        duplicate.original_ids.append(str(raw_q.id))
                        duplicate.updated_at = datetime.utcnow()
                        session.add(duplicate)
                        logger.info(f"Linked Raw Q {raw_q.id} to Existing Normalized Q {duplicate.id}")
                else:
                    # Create New Normalized Question
                    new_q = QuestionNormalized(
                        id=uuid4(),
                        base_form=normalized_text,
                        marks=raw_q.marks,
                        embedding=embedding,
                        original_ids=[str(raw_q.id)],
                        canonical_hash=get_canonical_hash(normalized_text),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(new_q)
                    logger.info(f"Created New Normalized Q {new_q.id}")
                
                # Mark Raw Question as Processed
                raw_q.processed = True
                raw_q.updated_at = datetime.utcnow()
                session.add(raw_q)
                
                processed_count += 1
                
                # Commit every 10 questions to save progress
                if processed_count % 10 == 0:
                    await session.commit()
            
            await session.commit()
            logger.info(f"Preprocessing complete. Processed {processed_count} questions.")
            
        except Exception as e:
            logger.error(f"Error in preprocessing: {e}")
            await session.rollback()
            raise
        break

