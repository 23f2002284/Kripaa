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
from src.sub_agents.question_generator_agent.prompts import (
    SHORT_ANSWER_VARIANT_PROMPT, SHORT_ANSWER_NOVEL_PROMPT,
    MEDIUM_ANSWER_VARIANT_PROMPT, MEDIUM_ANSWER_NOVEL_PROMPT,
    LONG_ANSWER_VARIANT_PROMPT, LONG_ANSWER_NOVEL_PROMPT
)

logger = get_logger()

# Section configurations
SECTION_CONFIGS = {
    "A": {
        "name": "Short Answer",
        "marks": 2,
        "target_count": 30,  # Generate 30, select 10
        "final_count": 10,
        "difficulty_range": [1, 2],
        "taxonomy": ["Remember", "Understand"],
        "strategy_weights": {"historical": 0.60, "variant": 0.25, "novel": 0.15},
        "temp_preference": [0.2, 0.5],  # Prefer conservative
        "variant_prompt": SHORT_ANSWER_VARIANT_PROMPT,
        "novel_prompt": SHORT_ANSWER_NOVEL_PROMPT
    },
    "B": {
        "name": "Medium Answer",
        "marks": 5,
        "target_count": 36,  # Generate 36, select 12
        "final_count": 12,
        "difficulty_range": [3],
        "taxonomy": ["Apply", "Analyze"],
        "strategy_weights": {"historical": 0.40, "variant": 0.35, "novel": 0.25},
        "temp_preference": [0.2, 0.5, 0.9],  # Mix
        "variant_prompt": MEDIUM_ANSWER_VARIANT_PROMPT,
        "novel_prompt": MEDIUM_ANSWER_NOVEL_PROMPT
    },
    "C": {
        "name": "Long Answer",
        "marks": 10,
        "target_count": 15,  # Generate 15, select 5
        "final_count": 5,
        "difficulty_range": [4, 5],
        "taxonomy": ["Evaluate", "Create"],
        "strategy_weights": {"historical": 0.30, "variant": 0.30, "novel": 0.40},
        "temp_preference": [0.5, 0.9],  # Prefer creative
        "variant_prompt": LONG_ANSWER_VARIANT_PROMPT,
        "novel_prompt": LONG_ANSWER_NOVEL_PROMPT
    }
}

async def generate_candidates_for_section(
    snapshot_id: UUID,
    section_name: str,
    section_config: dict,
    topic_vg_map: dict,
    stats: dict,
    session
) -> List[PredictionCandidate]:
    """Generate candidates for a specific section using multi-temperature strategy."""
    
    logger.info(f"Generating {section_config['target_count']} candidates for Section {section_name}...")
    
    candidates = []
    target_count = section_config['target_count']
    strategy_weights = section_config['strategy_weights']
    temp_options = section_config['temp_preference']
    
    # Create weighted strategy list for random selection
    strategies = (
        ["historical"] * int(strategy_weights["historical"] * 100) +
        ["variant"] * int(strategy_weights["variant"] * 100) +
        ["novel"] * int(strategy_weights["novel"] * 100)
    )
    
    # Get all topics
    topics = [tid for tid in stats.keys() if tid != "_meta"]
    
    generated_count = 0
    attempts = 0
    max_attempts = target_count * 3  # Prevent infinite loops
    
    while generated_count < target_count and attempts < max_attempts:
        attempts += 1
        
        # Pick a random topic
        if not topics:
            logger.warning("No topics found in stats. Skipping generation.")
            break
            
        topic_id = random.choice(topics)
        topic_data = stats[topic_id]
        topic_name = topic_data.get("name", "Unknown Topic")
        module_name = topic_data.get("module", "Unknown Module")
        gap_score = topic_data.get("gap_score", 0)
        status = topic_data.get("status", "stable")
        
        # Pick strategy
        strategy = random.choice(strategies)
        
        # Pick temperature
        temp = random.choice(temp_options)
        llm = get_llm(model_name="gemini-2.5-pro", temperature=temp)
        
        # Get available questions for this topic
        vgs = topic_vg_map.get(topic_id, [])
        available_questions = [q for vg in vgs for q in vg.questions]
        
        candidate_q = None
        origin_type = "historical"
        
        try:
            if strategy == "historical" and available_questions:
                # Select a historical question
                # Filter by difficulty if possible
                filtered = [q for q in available_questions if q.difficulty in section_config['difficulty_range']]
                if not filtered:
                    filtered = available_questions
                
                if filtered:
                    candidate_q = random.choice(filtered)
                    origin_type = "historical"
                else:
                    logger.warning(f"No historical questions available for topic {topic_name} in difficulty range {section_config['difficulty_range']}")
                    continue
                
            elif strategy == "variant" and available_questions:
                # Pick a question to rewrite
                if not available_questions:
                    logger.warning(f"No questions available for variant generation in topic {topic_name}")
                    continue
                    
                base_q = random.choice(available_questions)
                
                # Generate Variant using section-specific prompt
                chain = section_config['variant_prompt'] | llm
                response = await chain.ainvoke({"original_question": base_q.base_form})
                new_text = response.content.strip()
                
                # Save new question
                candidate_q = QuestionNormalized(
                    base_form=new_text,
                    difficulty=section_config['difficulty_range'][0],  # Assign section difficulty
                    taxonomy=section_config['taxonomy'],
                    canonical_hash="generated_variant",
                    embedding=[0.0]*768,
                    variant_group_id=base_q.variant_group_id
                )
                session.add(candidate_q)
                await session.flush()
                origin_type = "generated_variant"
                
            elif strategy == "novel":
                # Generate Novel Question using section-specific prompt
                chain = section_config['novel_prompt'] | llm
                response = await chain.ainvoke({
                    "topic_name": topic_name,
                    "module_name": module_name
                })
                new_text = response.content.strip()
                
                # Pick a variant group to link to
                target_vg = vgs[0] if vgs else None
                vg_id = target_vg.id if target_vg else None
                
                # Save new question
                candidate_q = QuestionNormalized(
                    base_form=new_text,
                    difficulty=section_config['difficulty_range'][0],
                    taxonomy=section_config['taxonomy'],
                    canonical_hash="generated_novel",
                    embedding=[0.0]*768,
                    variant_group_id=vg_id
                )
                session.add(candidate_q)
                await session.flush()
                origin_type = "generated_novel"
            
            # Fallback if strategy failed
            if not candidate_q and available_questions:
                candidate_q = random.choice(available_questions)
                origin_type = "historical_fallback"
            
            if candidate_q:
                candidate = PredictionCandidate(
                    normalized_question_id=candidate_q.id,
                    trend_snapshot_id=snapshot_id,
                    status=CandidateStatus.pending,
                    scores_json={
                        "section_target": section_name,
                        "section_marks": section_config['marks'],
                        "llm_temperature": temp,
                        "generation_strategy": strategy,
                        "origin": origin_type,
                        "gap_score": gap_score,
                        "trend_status": status,
                        "topic_name": topic_name
                    }
                )
                session.add(candidate)
                candidates.append(candidate)
                generated_count += 1
                
                if generated_count % 5 == 0:
                    logger.info(f"Section {section_name}: {generated_count}/{target_count} candidates generated")
                    
        except Exception as e:
            logger.warning(f"Failed to generate candidate: {e}")
            continue
    
    logger.info(f"Section {section_name}: Generated {generated_count} candidates (strategy: {dict(zip(['H','V','N'], [int(strategy_weights[k]*100) for k in ['historical','variant','novel']]))}%)")
    return candidates

async def generate_candidates_multi_section(snapshot_id: UUID, target_year: int) -> Dict[str, List[PredictionCandidate]]:
    """
    Generates prediction candidates for all sections using multi-temperature ensemble.
    Returns a dictionary mapping section names to candidate lists.
    """
    logger.info(f"Starting Multi-Section Ensemble Generation for {target_year}...")
    
    async for session in get_session():
        try:
            # Load Snapshot
            stmt = select(TrendSnapshot).where(TrendSnapshot.id == snapshot_id)
            result = await session.execute(stmt)
            snapshot = result.scalar_one_or_none()
            
            if not snapshot:
                logger.error(f"Snapshot {snapshot_id} not found.")
                return {}
            
            stats = snapshot.topic_stats_json
            
            # Fetch VariantGroups
            stmt_vg = select(VariantGroup).options(
                selectinload(VariantGroup.questions),
                selectinload(VariantGroup.syllabus_node)
            ).where(VariantGroup.syllabus_node_id != None)
            
            result_vg = await session.execute(stmt_vg)
            variant_groups = result_vg.scalars().all()
            
            # Build topic -> variant groups map
            topic_vg_map = {}
            for vg in variant_groups:
                if vg.syllabus_node_id:
                    tid = str(vg.syllabus_node_id)
                    if tid not in topic_vg_map:
                        topic_vg_map[tid] = []
                    topic_vg_map[tid].append(vg)
            
            # Generate for each section
            section_results = {}
            for section_name, section_config in SECTION_CONFIGS.items():
                candidates = await generate_candidates_for_section(
                    snapshot_id=snapshot_id,
                    section_name=section_name,
                    section_config=section_config,
                    topic_vg_map=topic_vg_map,
                    stats=stats,
                    session=session
                )
                section_results[section_name] = candidates
            
            await session.commit()
            
            total = sum(len(candidates) for candidates in section_results.values())
            logger.info(f"Generated {total} total candidates across all sections.")
            logger.info(f"Section A: {len(section_results['A'])}, B: {len(section_results['B'])}, C: {len(section_results['C'])}")
            
            return section_results

        except Exception as e:
            logger.error(f"Error in multi-section generation: {e}")
            await session.rollback()
            raise
        break

if __name__ == "__main__":
    pass
