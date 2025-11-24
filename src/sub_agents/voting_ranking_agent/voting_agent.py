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

# Section targets matching generation
SECTION_TARGETS = {
    "A": {"final_count": 10, "marks": 2, "max_per_topic": 3},
    "B": {"final_count": 12, "marks": 5, "max_per_topic": 3},
    "C": {"final_count": 5, "marks": 10, "max_per_topic": 2}
}

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
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

async def vote_section(
    candidates: List[PredictionCandidate],
    section_name: str,
    section_config: dict,
    session
) -> List[PredictionCandidate]:
    """Vote and select candidates for a specific section."""
    
    logger.info(f"Section {section_name}: Processing {len(candidates)} candidates...")
    
    target_count = section_config['final_count']
    max_per_topic = section_config['max_per_topic']
    
    # Generate embeddings and calculate relevance
    scored_candidates = []
    
    for cand in candidates:
        q = cand.normalized_question
        
        # Generate embedding if missing
        needs_embedding = False
        if q.embedding is None:
            needs_embedding = True
        elif isinstance(q.embedding, list) and (not q.embedding or all(x == 0 for x in q.embedding)):
            needs_embedding = True
        elif hasattr(q.embedding, 'any'):
             if q.embedding.size == 0 or not np.any(q.embedding):
                needs_embedding = True
        
        if needs_embedding:
            logger.info(f"Generating embedding for {cand.id}...")
            emb = await generate_embedding(q.base_form)
            q.embedding = emb
            session.add(q)
        
        # Calculate relevance
        relevance = 0.0
        topic_id = "unknown"
        
        if q.variant_group and q.variant_group.syllabus_node:
            topic_node = q.variant_group.syllabus_node
            topic_id = str(topic_node.id)
            if topic_node.embedding is not None:
                 has_emb = False
                 if isinstance(topic_node.embedding, list) and topic_node.embedding:
                     has_emb = True
                 elif hasattr(topic_node.embedding, 'any') and topic_node.embedding.size > 0:
                     has_emb = True
                     
                 if has_emb:
                    relevance = cosine_similarity(q.embedding, topic_node.embedding)
        
        # Update scores
        scores = dict(cand.scores_json) if cand.scores_json else {}
        scores["relevance_score"] = round(relevance, 3)
        
        # Calculate final score
        gap = scores.get("gap_score", 0)
        final_score = (gap / 20.0) + relevance
        scores["final_score"] = round(final_score, 3)
        
        cand.scores_json = scores
        
        scored_candidates.append({
            "candidate": cand,
            "score": final_score,
            "topic_id": topic_id,
            "relevance": relevance
        })
    
    # Sort by score
    scored_candidates.sort(key=lambda x: x["score"], reverse=True)
    
    # Apply filters
    selected = []
    topic_counts = {}
    
    for item in scored_candidates:
        cand = item["candidate"]
        topic_id = item["topic_id"]
        scores = dict(cand.scores_json)
        
        # Filter: Relevance threshold
        if item["relevance"] < 0.5:
            cand.status = CandidateStatus.excluded
            scores["exclusion_reason"] = f"Low Relevance ({item['relevance']:.2f})"
            scores["exclusion_category"] = "Low Relevance"
            cand.scores_json = scores
            session.add(cand)
            continue
        
        # Filter: Difficulty verification
        expected_diff = cand.normalized_question.difficulty
        if section_name == "A" and expected_diff not in [1, 2]:
            cand.status = CandidateStatus.excluded
            scores["exclusion_reason"] = f"Difficulty Mismatch (got {expected_diff}, expected 1-2 for Section A)"
            scores["exclusion_category"] = "Section Mismatch"
            cand.scores_json = scores
            session.add(cand)
            continue
        
        # Filter: Topic cap
        if topic_counts.get(topic_id, 0) >= max_per_topic:
            cand.status = CandidateStatus.excluded
            scores["exclusion_reason"] = f"Topic Cap ({max_per_topic} max per topic)"
            scores["exclusion_category"] = "Topic Cap"
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
            scores["exclusion_reason"] = f"Rank Cutoff (Rel: {item['relevance']:.2f})"
            scores["exclusion_category"] = "Rank Cutoff"
            cand.scores_json = scores
            session.add(cand)
    
    logger.info(f"Section {section_name}: Selected {len(selected)}/{target_count}")
    return selected

async def run_voting_process_multi_section(snapshot_id: UUID):
    """
    Section-aware voting process.
    Votes for each section independently.
    """
    logger.info(f"Starting Section-Aware Voting for Snapshot {snapshot_id}...")
    
    async for session in get_session():
        try:
            # Fetch all candidates
            stmt = select(PredictionCandidate).options(
                selectinload(PredictionCandidate.normalized_question).selectinload(QuestionNormalized.variant_group).selectinload(VariantGroup.syllabus_node)
            ).where(PredictionCandidate.trend_snapshot_id == snapshot_id)
            
            result = await session.execute(stmt)
            all_candidates = result.scalars().all()
            
            if not all_candidates:
                logger.warning("No candidates found.")
                return {}
            
            logger.info(f"Total candidates: {len(all_candidates)}")
            
            # Group by section - only process candidates with section_target
            section_groups = {"A": [], "B": [], "C": []}
            skipped_old = 0
            
            for cand in all_candidates:
                section_target = cand.scores_json.get("section_target")
                if section_target and section_target in section_groups:
                    section_groups[section_target].append(cand)
                else:
                    # Skip old candidates without section_target
                    skipped_old += 1
            
            if skipped_old > 0:
                logger.info(f"Skipped {skipped_old} old candidates without section_target")
            
            logger.info(f"Section distribution: A={len(section_groups['A'])}, B={len(section_groups['B'])}, C={len(section_groups['C'])}")
            
            # Vote per section
            all_selected = {}
            for section_name, candidates in section_groups.items():
                if not candidates:
                    logger.warning(f"No candidates for Section {section_name}")
                    continue
                
                section_config = SECTION_TARGETS[section_name]
                selected = await vote_section(candidates, section_name, section_config, session)
                all_selected[section_name] = selected
            
            await session.commit()
            
            total_selected = sum(len(s) for s in all_selected.values())
            logger.info(f"Voting Complete. Total selected: {total_selected}")
            logger.info(f"Section A: {len(all_selected.get('A', []))}, B: {len(all_selected.get('B', []))}, C: {len(all_selected.get('C', []))}")
            
            return all_selected

        except Exception as e:
            logger.error(f"Error in voting process: {e}")
            await session.rollback()
            raise
        break

if __name__ == "__main__":
    pass
