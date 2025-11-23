import asyncio
import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import select, func
from src.data_models.models import VariantGroup, CompositeQuestion
from src.sub_agents.composite_question_agent.composite_agent import process_composites
from utils.db import get_session

@pytest.mark.asyncio
async def test_composite_generation_real_data():
    """
    Verify that the composite agent correctly generates questions from variant groups.
    """
    
    async for session in get_session():
        # 1. Check initial state
        stmt = select(func.count()).select_from(VariantGroup)
        result = await session.execute(stmt)
        group_count = result.scalar()
        
        print(f"Total Variant Groups available: {group_count}")
        
        if group_count == 0:
            print("No variant groups found. Please run variant grouping first.")
            return

    # 2. Run Agent
    print("\n--- Running Composite Generation (First Pass) ---")
    await process_composites()
    
    # 3. Verify Results
    async for session in get_session():
        # Check Composite Questions count
        stmt = select(func.count()).select_from(CompositeQuestion)
        result = await session.execute(stmt)
        composite_count_1 = result.scalar()
        
        print(f"Total Composite Questions (Pass 1): {composite_count_1}")
        
        # Show some samples
        stmt = select(CompositeQuestion).limit(5)
        result = await session.execute(stmt)
        samples = result.scalars().all()
        
        print("\nSample Composite Questions:")
        for c in samples:
            print(f"ID: {c.id}")
            print(f"Title: {c.title}")
            print(f"Constructed Stem: {c.constructed_stem[:100]}...")
            print(f"Parts Count: {len(c.parts)}")
            print(f"Source Group ID: {c.source_variant_group_id}")
            
            assert c.source_variant_group_id is not None, "Source Variant Group ID should be populated"
            print("-" * 20)

    # 4. Idempotency Check
    print("\n--- Running Composite Generation (Second Pass - Idempotency) ---")
    await process_composites()
    
    async for session in get_session():
        stmt = select(func.count()).select_from(CompositeQuestion)
        result = await session.execute(stmt)
        composite_count_2 = result.scalar()
        
        print(f"Total Composite Questions (Pass 2): {composite_count_2}")
        
        assert composite_count_1 == composite_count_2, "Composite count should not change (Idempotency check)"
        print("SUCCESS: Idempotency verified.")

if __name__ == "__main__":
    asyncio.run(test_composite_generation_real_data())
