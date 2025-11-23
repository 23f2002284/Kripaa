import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
import pytest
from sqlalchemy import select, func
from src.data_models.models import QuestionRaw, QuestionNormalized
from src.sub_agents.question_preprocessing_agent.question_preprocessing_agent import process_questions
from utils.db import get_session

@pytest.mark.asyncio
async def test_preprocessing_real_data():
    """
    Verify that the preprocessing agent correctly processes real data from the database.
    """
    
    async for session in get_session():
        # 1. Check initial state
        stmt = select(func.count()).select_from(QuestionRaw).where(QuestionRaw.processed == False)
        result = await session.execute(stmt)
        initial_unprocessed = result.scalar()
        
        print(f"Initial unprocessed questions: {initial_unprocessed}")
        
        if initial_unprocessed == 0:
            print("No unprocessed questions found. Please ensure QuestionRaw has data with processed=False.")
            return

    # 2. Run Agent
    await process_questions()
    
    # 3. Verify Results
    async for session in get_session():
        # Check remaining unprocessed
        stmt = select(func.count()).select_from(QuestionRaw).where(QuestionRaw.processed == False)
        result = await session.execute(stmt)
        remaining_unprocessed = result.scalar()
        
        print(f"Remaining unprocessed questions: {remaining_unprocessed}")
        assert remaining_unprocessed == 0, "All questions should be processed"
        
        # Check Normalized Questions count
        stmt = select(func.count()).select_from(QuestionNormalized)
        result = await session.execute(stmt)
        normalized_count = result.scalar()
        
        print(f"Total Normalized Questions: {normalized_count}")
        
        # Show some samples
        stmt = select(QuestionNormalized).limit(5)
        result = await session.execute(stmt)
        samples = result.scalars().all()
        
        print("\nSample Normalized Questions:")
        for q in samples:
            print(f"ID: {q.id}")
            print(f"Base Form: {q.base_form[:100]}...")
            print(f"Original IDs: {len(q.original_ids)}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_preprocessing_real_data())
