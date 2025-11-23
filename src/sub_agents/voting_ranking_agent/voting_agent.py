import asyncio
import numpy as np
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from utils.db import get_session
from utils.logger import get_logger
from utils.llm import generate_embedding
from src.data_models.models import (
    TrendSnapshot,
    PredictionCandidate,
    CandidateStatus,
    QuestionNormalized,
    VariantGroup,
    SyllabusNode
)

logger = get_logger()

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    # Handle numpy ambiguity
    if v1 is None or v2 is None: return 0.0
    if hasattr(v1, 'size') and v1.size == 0: return 0.0
    if hasattr(v2, 'size') and v2.size == 0: return 0.0
    if isinstance(v1, list) and not v1: return 0.0
    if isinstance(v2, list) and not v2: return 0.0
    vec1 = np.array(v1)
    vec2 = np.array(v2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0: return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))

async def run_voting_process(snapshot_id: UUID, target_count: int = 25):
    """
    Filters and ranks candidates to select the final set for the sample paper.
    """
    logger.info(f"Starting Voting Process for Snapshot {snapshot_id}...")
    
    async for session in get_session():
        try:
            # 1. Fetch Candidates
            stmt = select(PredictionCandidate).options(
                selectinload(PredictionCandidate.normalized_question).selectinload(QuestionNormalized.variant_group).selectinload(VariantGroup.syllabus_node)
            ).where(PredictionCandidate.trend_snapshot_id == snapshot_id)
            
            result = await session.execute(stmt)
            candidates = result.scalars().all()
            
            if not candidates:
                logger.warning("No candidates found.")
                return

            logger.info(f"Processing {len(candidates)} candidates...")
            
            # 2. Generate Embeddings & Calculate Relevance
            updates = []
            scored_candidates = []
            
            for cand in candidates:
                q = cand.normalized_question
                
                # Generate embedding if missing (e.g. for Novel/Variant)
                # Check if it's a zero vector or empty
                # Handle both list and numpy array
                needs_embedding = False
                if q.embedding is None:
                    needs_embedding = True
                elif isinstance(q.embedding, list) and (not q.embedding or all(x == 0 for x in q.embedding)):
                    needs_embedding = True
                elif hasattr(q.embedding, 'any'): # Numpy array
                     if q.embedding.size == 0 or not np.any(q.embedding):
                        needs_embedding = True
                
                if needs_embedding:
                    logger.info(f"Generating embedding for Candidate {cand.id} ({cand.scores_json.get('origin')})...")
                    emb = await generate_embedding(q.base_form)
                    q.embedding = emb
                    session.add(q) # Mark for update
                
                # Calculate Relevance
                relevance = 0.0
                topic_id = "unknown"
                
                if q.variant_group and q.variant_group.syllabus_node:
                    topic_node = q.variant_group.syllabus_node
                    topic_id = str(topic_node.id)
                    if topic_node.embedding is not None:
                         # Handle numpy array check
                         has_emb = False
                         if isinstance(topic_node.embedding, list) and topic_node.embedding:
                             has_emb = True
                         elif hasattr(topic_node.embedding, 'any') and topic_node.embedding.size > 0:
                             has_emb = True
                             
                         if has_emb:
                            relevance = cosine_similarity(q.embedding, topic_node.embedding)
                
                # Create a copy to ensure change detection
                scores = dict(cand.scores_json) if cand.scores_json else {}
                
                # Update scores
                scores["relevance_score"] = round(relevance, 3)
                
                # Calculate Final Score
                # Score = Prob + Gap/20 + Relevance
                prob = scores.get("selection_probability", 0.5)
                gap = scores.get("gap_score", 0)
                
                final_score = prob + (gap / 20.0) + relevance
                scores["final_score"] = round(final_score, 3)
                
                cand.scores_json = scores # Re-assign
                
                scored_candidates.append({
                    "candidate": cand,
                    "score": final_score,
                    "topic_id": topic_id,
                    "relevance": relevance
                })
            
            # 3. Apply Filters & Selection
            # Sort by score desc
            scored_candidates.sort(key=lambda x: x["score"], reverse=True)
            
            selected = []
            topic_counts = {}
            
            for item in scored_candidates:
                cand = item["candidate"]
                topic_id = item["topic_id"]
                scores = dict(cand.scores_json) # Copy again for filter updates
                
                # Filter: Relevance Threshold
                # Lowering threshold to 0.5 to allow more candidates initially
                if item["relevance"] < 0.5: 
                    cand.status = CandidateStatus.excluded
                    scores["exclusion_reason"] = f"Low Relevance ({item['relevance']:.2f})"
                    cand.scores_json = scores
                    session.add(cand) 
                    continue
                
                # Filter: Diversity (Max 2 per topic)
                if topic_counts.get(topic_id, 0) >= 2:
                    cand.status = CandidateStatus.excluded
                    scores["exclusion_reason"] = f"Topic Cap Exceeded ({topic_id})"
                    cand.scores_json = scores
                    session.add(cand) 
                    continue
                
                # Select
                if len(selected) < target_count:
                    cand.status = CandidateStatus.selected
                    selected.append(cand)
                    topic_counts[topic_id] = topic_counts.get(topic_id, 0) + 1
                    session.add(cand) 
                else:
                    cand.status = CandidateStatus.excluded
                    scores["exclusion_reason"] = "Rank Cutoff"
                    cand.scores_json = scores
                    session.add(cand)
            
            await session.commit()
            logger.info(f"Voting Complete. Selected {len(selected)} candidates.")
            return selected

        except Exception as e:
            logger.error(f"Error in voting process: {e}")
            await session.rollback()
            raise
        break

if __name__ == "__main__":
    pass
