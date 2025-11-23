import asyncio
import random
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from utils.db import get_session
from utils.logger import get_logger
from utils.llm import get_llm
from src.data_models.models import (
    TrendSnapshot,
    PredictionCandidate,
    VariantGroup,
    QuestionNormalized,
    CandidateStatus,
    QuestionRaw
)
from src.sub_agents.question_generator_agent.prompts import VARIANT_GENERATION_PROMPT, NOVEL_GENERATION_PROMPT

logger = get_logger()

async def generate_candidates(snapshot_id: UUID, target_year: int) -> List[PredictionCandidate]:
    """
    Generates prediction candidates using Ensemble Strategies:
    1. Historical: Smart selection from existing questions.
    2. Variant: LLM-rewritten version of an existing question.
    3. Novel: LLM-created new question for a topic.
    """
    logger.info(f"Starting Ensemble Candidate Generation for {target_year}...")
    
    llm = get_llm(temperature=0.7) # Higher temp for creativity in variants/novel
    
    async for session in get_session():
        try:
            # 1. Load Snapshot
            stmt = select(TrendSnapshot).where(TrendSnapshot.id == snapshot_id)
            result = await session.execute(stmt)
            snapshot = result.scalar_one_or_none()
            
            if not snapshot:
                logger.error(f"Snapshot {snapshot_id} not found.")
                return []
            
            stats = snapshot.topic_stats_json
            candidates = []
            
            # 2. Fetch VariantGroups
            stmt_vg = select(VariantGroup).options(
                selectinload(VariantGroup.questions),
                selectinload(VariantGroup.syllabus_node)
            ).where(VariantGroup.syllabus_node_id != None)
            
            result_vg = await session.execute(stmt_vg)
            variant_groups = result_vg.scalars().all()
            
            topic_vg_map = {}
            for vg in variant_groups:
                if vg.syllabus_node_id:
                    tid = str(vg.syllabus_node_id)
                    if tid not in topic_vg_map:
                        topic_vg_map[tid] = []
                    topic_vg_map[tid].append(vg)
            
            selected_count = 0
            
            for topic_id, topic_data in stats.items():
                if topic_id == "_meta": continue
                
                status = topic_data.get("status", "stable")
                gap_score = topic_data.get("gap_score", 0)
                topic_name = topic_data.get("name", "Unknown Topic")
                module_name = topic_data.get("module", "Unknown Module")
                
                # Determine Strategy based on Status/Gap
                # Emerging/High Gap -> High chance of Novel or Variant
                # Stable -> High chance of Historical or Variant
                # Declining -> Low chance, mostly Historical if any
                
                strategies = []
                
                if status == "emerging" or gap_score > 5:
                    # 40% Novel, 40% Variant, 20% Historical
                    strategies = ["novel"] * 4 + ["variant"] * 4 + ["historical"] * 2
                elif status == "stable":
                    # 10% Novel, 40% Variant, 50% Historical
                    strategies = ["novel"] * 1 + ["variant"] * 4 + ["historical"] * 5
                else: # declining
                    # 10% Variant, 90% Historical (if selected at all)
                    strategies = ["variant"] * 1 + ["historical"] * 9
                
                # Base probability to pick this topic at all
                base_prob = 0.3
                if status == "emerging": base_prob += 0.4
                if gap_score > 5: base_prob += 0.4
                elif gap_score > 0: base_prob += 0.2
                if status == "declining": base_prob -= 0.2
                
                prob = max(0.05, min(0.95, base_prob))
                
                if random.random() < prob:
                    strategy = random.choice(strategies)
                    
                    # Get available questions for this topic
                    vgs = topic_vg_map.get(topic_id, [])
                    available_questions = [q for vg in vgs for q in vg.questions]
                    
                    candidate_q = None
                    origin_type = "historical"
                    
                    if strategy == "historical" and available_questions:
                        # Smart Selection: Pick most recent or random
                        # For now, random is fine as a baseline
                        candidate_q = random.choice(available_questions)
                        origin_type = "historical"
                        
                    elif strategy == "variant" and available_questions:
                        # Pick a question to rewrite
                        base_q = random.choice(available_questions)
                        
                        # Generate Variant
                        chain = VARIANT_GENERATION_PROMPT | llm
                        response = await chain.ainvoke({"original_question": base_q.base_form})
                        new_text = response.content.strip()
                        
                        # Save new question
                        candidate_q = QuestionNormalized(
                            base_form=new_text,
                            difficulty=base_q.difficulty,
                            taxonomy=base_q.taxonomy,
                            canonical_hash="generated_variant", # Placeholder
                            embedding=[0.0]*768, # Placeholder
                            variant_group_id=base_q.variant_group_id # Link to original group
                        )
                        session.add(candidate_q)
                        await session.flush() # Get ID
                        origin_type = "generated_variant"
                        
                    elif strategy == "novel":
                        # Generate Novel Question
                        chain = NOVEL_GENERATION_PROMPT | llm
                        response = await chain.ainvoke({
                            "topic_name": topic_name,
                            "module_name": module_name,
                            "difficulty": "3", # Default to medium
                            "taxonomy": "Apply" # Default to application
                        })
                        new_text = response.content.strip()
                        
                        # Pick a variant group to link to (to establish topic)
                        # We can pick the first one from the list we fetched
                        target_vg = vgs[0] if vgs else None
                        vg_id = target_vg.id if target_vg else None
                        
                        # Save new question
                        candidate_q = QuestionNormalized(
                            base_form=new_text,
                            difficulty=3,
                            taxonomy=["Apply"],
                            canonical_hash="generated_novel",
                            embedding=[0.0]*768,
                            variant_group_id=vg_id # Link to topic group
                        )
                        session.add(candidate_q)
                        await session.flush()
                        origin_type = "generated_novel"
                    
                    # Fallback if strategy failed (e.g. no questions for variant)
                    if not candidate_q and available_questions:
                        candidate_q = random.choice(available_questions)
                        origin_type = "historical_fallback"
                    
                    if candidate_q:
                        candidate = PredictionCandidate(
                            normalized_question_id=candidate_q.id,
                            trend_snapshot_id=snapshot.id,
                            status=CandidateStatus.pending,
                            scores_json={
                                "selection_probability": round(prob, 2),
                                "gap_score": gap_score,
                                "trend_status": status,
                                "strategy": strategy,
                                "origin": origin_type
                            }
                        )
                        session.add(candidate)
                        candidates.append(candidate)
                        selected_count += 1
            
            await session.commit()
            logger.info(f"Generated {selected_count} candidates using Ensemble Strategies.")
            return candidates

        except Exception as e:
            logger.error(f"Error in candidate generation: {e}")
            await session.rollback()
            raise
        break
