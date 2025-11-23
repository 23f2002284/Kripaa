import asyncio
from sqlalchemy import select
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import get_session
from src.data_models.models import QuestionNormalized
from src.sub_agents.syll_mapping_tag_agent.tagging_agent import tag_questions

async def verify_tagging():
    print("--- Verifying Tagging Agent ---")
    
    # 1. Check initial state
    async for session in get_session():
        stmt = select(QuestionNormalized).where(QuestionNormalized.difficulty != None)
        result = await session.execute(stmt)
        initial_tagged = len(result.scalars().all())
        print(f"Initially tagged questions: {initial_tagged}")
        break
    
    # 2. Run Tagging Agent
    print("\nRunning Tagging Agent...")
    await tag_questions(batch_size=5)
    
    # 3. Check final state
    async for session in get_session():
        stmt = select(QuestionNormalized).where(QuestionNormalized.difficulty != None)
        result = await session.execute(stmt)
        tagged_questions = result.scalars().all()
        final_tagged = len(tagged_questions)
        print(f"\nFinal tagged questions: {final_tagged}")
        
        if tagged_questions:
            print("\nSample Tags:")
            for q in tagged_questions[:5]:
                print(f"Q: {q.base_form[:50]}...")
                print(f"   Difficulty: {q.difficulty}")
                print(f"   Taxonomy: {q.taxonomy}")
                print("-" * 20)
        break

if __name__ == "__main__":
    asyncio.run(verify_tagging())
