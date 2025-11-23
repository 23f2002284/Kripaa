import asyncio
from typing import List
from uuid import uuid4
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from utils.db import get_session
from utils.logger import get_logger
from utils.llm import get_default_llm

from src.data_models.models import (
    QuestionNormalized,
    VariantGroup,
    CompositeQuestion,
)

from src.sub_agents.composite_question_agent.prompts import COMPOSITE_MASTER_PROMPT

logger = get_logger()


# ============================================================
# LLM CALL
# ============================================================

async def generate_composite_question(canonical_stem: str, variants: List[str]) -> str:
    """
    Generate a composite master question using the LLM.
    If variants is empty, fall back to canonical stem.
    """
    if not variants:
        return canonical_stem

    llm = get_default_llm()
    chain = COMPOSITE_MASTER_PROMPT | llm

    variants_str = "\n".join([f"- {v}" for v in variants])

    try:
        response = await chain.ainvoke({
            "canonical_stem": canonical_stem,
            "variants": variants_str
        })
        return response.content.strip()

    except Exception as e:
        logger.error(f"LLM ERROR (Composite Question): {e}")
        return canonical_stem



# ============================================================
# CORE: Composite Generator
# ============================================================

async def generate_for_group(session: AsyncSession, group: VariantGroup):
    """
    Generate composite question for a single VariantGroup.

    Idempotent:
    - If this group already has a composite, skip.
    """

    # 1. Check if already exists (ID-based check to avoid expensive scans)
    exists_stmt = select(func.count()).select_from(CompositeQuestion).where(
        CompositeQuestion.source_variant_group_id == group.id
    )
    exists_result = await session.execute(exists_stmt)
    if exists_result.scalar() > 0:
        logger.debug(f"Skipping group {group.id}, composite already generated.")
        return None

    # 2. Fetch questions belonging to this group
    q_stmt = select(QuestionNormalized).where(
        QuestionNormalized.variant_group_id == group.id
    )
    q_res = await session.execute(q_stmt)
    questions = q_res.scalars().all()

    if not questions:
        logger.debug(f"Group {group.id} has no questions. Skipping.")
        return None

    variant_texts = [q.base_form for q in questions]

    # 3. Generate composite question
    # OPTIMIZATION: If only 1 variant, no need for LLM. The canonical stem + the single variant is enough.
    # Actually, if only 1 variant, the composite IS that variant (or the stem).
    # Let's just use the variant text itself as the composite if it's a singleton, 
    # OR use the canonical stem if it's better.
    # User rule: "Master Composite Question".
    # If 1 variant, the "Composite" is just that question.
    
    if len(questions) == 1:
        composite_text = questions[0].base_form
        logger.debug(f"Singleton group {group.id}: Using variant text directly.")
    else:
        composite_text = await generate_composite_question(group.canonical_stem, variant_texts)

    # 4. Create CompositeQuestion entry
    part_ids = [str(q.id) for q in questions]

    composite = CompositeQuestion(
        id=uuid4(),
        title=group.canonical_stem,
        constructed_stem=composite_text,
        parts=part_ids,
        source_variant_group_id=group.id,    # explicitly link
        created_at=datetime.utcnow()
    )

    session.add(composite)
    return composite



# ============================================================
# MAIN DRIVER
# ============================================================

async def process_composites():
    """
    Orchestrates composite question generation for all VariantGroups.

    - Runs once per batch.
    - Safe to run multiple times due to idempotency checks.
    - Commits periodically to keep memory low.
    """

    logger.info("▶ Starting Composite Question Generation")

    async for session in get_session():

        try:
            # Fetch all groups
            stmt = select(VariantGroup)
            result = await session.execute(stmt)
            groups = result.scalars().all()

            logger.info(f"Found {len(groups)} variant groups to evaluate.")

            created = 0

            for idx, group in enumerate(groups):

                composite = await generate_for_group(session, group)
                if composite:
                    created += 1
                    logger.info(f"✓ Created Composite: {composite.id} | Group: {group.id}")

                # Commit every 10 groups
                if idx % 10 == 0:
                    await session.commit()

            await session.commit()
            logger.info(f"✔ Composite Generation Complete. Created: {created}")

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Composite Generation Failure: {e}")
            raise

        break  # exit async generator