import asyncio
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector

from utils.db import get_session
from utils.logger import get_logger
from utils.llm import get_default_llm
from src.data_models.models import QuestionNormalized, VariantGroup
from utils.settings import settings
from src.sub_agents.question_preprocessing_agent.prompts import CONCEPT_STEM_PROMPT

logger = get_logger()

# Threshold for grouping (lower than deduplication)
GROUPING_THRESHOLD = settings.variant_grouping_threshold

async def generate_canonical_stem(questions: List[str]) -> str:
    """
    Generate a canonical stem for a list of questions using an LLM.
    """
    if not questions:
        return ""
    
    # If only one question, just return it (cleaned)
    if len(questions) == 1:
        return questions[0]
    
    llm = get_default_llm()
    chain = CONCEPT_STEM_PROMPT | llm
    
    # Format questions as a bulleted list
    questions_str = "\n".join([f"- {q}" for q in questions])
    
    try:
        response = await chain.ainvoke({"questions": questions_str})
        return response.content.strip()
    except Exception as e:
        logger.error(f"Error generating canonical stem: {e}")
        # Fallback to the first question
        return questions[0]

async def process_grouping():
    """
    Main loop to group normalized questions into VariantGroups.
    """
    logger.info("Starting Variant Grouping...")
    
    async for session in get_session():
        try:
            # 1. Fetch Ungrouped Questions
            stmt = select(QuestionNormalized).where(QuestionNormalized.variant_group_id == None)
            result = await session.execute(stmt)
            ungrouped_questions = result.scalars().all()
            
            logger.info(f"Found {len(ungrouped_questions)} ungrouped questions.")
            
            processed_ids = set()
            groups_created = 0
            groups_updated = 0
            
            for seed_q in ungrouped_questions:
                if seed_q.id in processed_ids:
                    continue
                
                processed_ids.add(seed_q.id)
                
                # 2. Find Neighbors (ALL questions, grouped or ungrouped)
                distance_threshold = 1 - GROUPING_THRESHOLD
                
                stmt = select(QuestionNormalized).where(
                    QuestionNormalized.id != seed_q.id,
                    QuestionNormalized.embedding.cosine_distance(seed_q.embedding) < distance_threshold
                )
                
                result = await session.execute(stmt)
                neighbors = result.scalars().all()
                
                # Check if any neighbor is already in a group
                existing_group_id = None
                for neighbor in neighbors:
                    if neighbor.variant_group_id:
                        existing_group_id = neighbor.variant_group_id
                        break
                
                if existing_group_id:
                    # JOIN EXISTING GROUP
                    seed_q.variant_group_id = existing_group_id
                    seed_q.updated_at = datetime.utcnow()
                    session.add(seed_q)
                    
                    # Update group stats
                    group = await session.get(VariantGroup, existing_group_id)
                    if group:
                        group.recurrence_count += 1
                        session.add(group)
                    
                    groups_updated += 1
                    logger.info(f"Joined Q {seed_q.id} to Existing Group {existing_group_id}")
                    
                else:
                    # CREATE NEW GROUP
                    cluster_questions = [seed_q]
                    
                    # Collect ungrouped neighbors for this new group
                    for neighbor in neighbors:
                        if neighbor.variant_group_id is None and neighbor.id not in processed_ids:
                            cluster_questions.append(neighbor)
                            processed_ids.add(neighbor.id)
                    
                    # Generate Canonical Stem
                    question_texts = [q.base_form for q in cluster_questions]
                    canonical_stem = await generate_canonical_stem(question_texts)
                    
                    new_group = VariantGroup(
                        id=uuid4(),
                        canonical_stem=canonical_stem,
                    slot_count=0, # To be updated later
                    recurrence_count=len(cluster_questions), # Initial count
                        created_at=datetime.utcnow()
                    )
                    session.add(new_group)
                    await session.flush()
                    
                    # Link questions to group
                    for q in cluster_questions:
                        q.variant_group_id = new_group.id
                        q.updated_at = datetime.utcnow()
                        session.add(q)
                    
                    groups_created += 1
                    logger.info(f"Created Group {new_group.id} with {len(cluster_questions)} variants. Stem: {canonical_stem}")
                
                # Commit every 5 operations
                if (groups_created + groups_updated) % 5 == 0:
                    await session.commit()
            
            await session.commit()
            logger.info(f"Grouping complete. Created {groups_created} groups, Updated {groups_updated} groups.")
            
        except Exception as e:
            logger.error(f"Error in grouping: {e}")
            await session.rollback()
            raise
        break
