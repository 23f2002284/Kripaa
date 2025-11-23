import asyncio
import pytest
from sqlalchemy import select, func
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_models.models import QuestionNormalized, VariantGroup
from src.sub_agents.question_preprocessing_agent.variant_grouping import process_grouping
from utils.db import get_session

@pytest.mark.asyncio
async def test_variant_grouping_real_data():
    """
    Verify that the variant grouping agent correctly groups normalized questions.
    """
    
    async for session in get_session():
        # 1. Check initial state
        stmt = select(func.count()).select_from(QuestionNormalized).where(QuestionNormalized.variant_group_id == None)
        result = await session.execute(stmt)
        initial_ungrouped = result.scalar()
        
        print(f"Initial ungrouped questions: {initial_ungrouped}")
        
        if initial_ungrouped == 0:
            print("No ungrouped questions found. Please ensure QuestionNormalized has data.")
            # We might want to reset some data for testing if needed, but for now let's assume data exists.
            return

    # 2. Run Agent
    await process_grouping()
    
    # 3. Verify Results
    async for session in get_session():
        # Check remaining ungrouped
        stmt = select(func.count()).select_from(QuestionNormalized).where(QuestionNormalized.variant_group_id == None)
        result = await session.execute(stmt)
        remaining_ungrouped = result.scalar()
        
        print(f"Remaining ungrouped questions: {remaining_ungrouped}")
        # Note: It's possible some questions are singletons and form their own groups, 
        # so remaining_ungrouped should ideally be 0 if we group singletons too.
        # Our logic creates a group for every seed, so yes, it should be 0.
        
        assert remaining_ungrouped == 0, "All questions should be grouped (even singletons)"
        
        # Check Groups count
        stmt = select(func.count()).select_from(VariantGroup)
        result = await session.execute(stmt)
        group_count = result.scalar()
        
        print(f"Total Variant Groups: {group_count}")
        
        # Show some samples
        stmt = select(VariantGroup).limit(5)
        result = await session.execute(stmt)
        samples = result.scalars().all()
        
        print("\nSample Variant Groups:")
        for g in samples:
            print(f"ID: {g.id}")
            print(f"Canonical Stem: {g.canonical_stem}")
            print(f"Recurrence Count: {g.recurrence_count}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_variant_grouping_real_data())
