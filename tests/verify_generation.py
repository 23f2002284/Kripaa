import asyncio
from sqlalchemy import select
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import get_session
from src.data_models.models import TrendSnapshot, PredictionCandidate
from src.sub_agents.question_generator_agent.question_generator_agent import generate_candidates

async def verify_generation():
    print("--- Verifying Question Generator Agent ---")
    
    snapshot_id = None
    
    # 1. Get the latest snapshot
    async for session in get_session():
        stmt = select(TrendSnapshot).order_by(TrendSnapshot.created_at.desc()).limit(1)
        result = await session.execute(stmt)
        snapshot = result.scalar_one_or_none()
        if snapshot:
            snapshot_id = snapshot.id
            print(f"Using Snapshot ID: {snapshot_id}")
        break
    
    if not snapshot_id:
        print("No snapshot found. Run verify_trends.py first.")
        return

    # 2. Clear existing candidates for this snapshot (to avoid duplicates during testing)
    from sqlalchemy import delete
    async for session in get_session():
        await session.execute(delete(PredictionCandidate).where(PredictionCandidate.trend_snapshot_id == snapshot_id))
        await session.commit()
        break
        
    # 3. Generate Candidates
    await generate_candidates(snapshot_id, 2025)
    
    # 3. Fetch and Inspect
    # We fetch from DB to ensure we can load relationships
    from sqlalchemy.orm import selectinload
    from src.data_models.models import QuestionNormalized
    
    async for session in get_session():
        stmt = select(PredictionCandidate).options(
            selectinload(PredictionCandidate.normalized_question)
        ).where(PredictionCandidate.trend_snapshot_id == snapshot_id)
        
        result = await session.execute(stmt)
        candidates = result.scalars().all()
        
        print(f"\nGenerated {len(candidates)} candidates.")
        
        print("\n--- Sample Candidates ---")
        for c in candidates[:10]: # Show more samples
            print(f"Candidate ID: {c.id}")
            print(f"Origin: {c.scores_json.get('origin', 'unknown')} ({c.scores_json.get('strategy', 'unknown')})")
            print(f"Question: {c.normalized_question.base_form[:100]}...")
            print(f"Scores: {c.scores_json}")
            print("-" * 20)
            
        # Stats
        origins = [c.scores_json.get('origin', 'unknown') for c in candidates]
        from collections import Counter
        print(f"\nOrigin Distribution: {Counter(origins)}")
        break

if __name__ == "__main__":
    asyncio.run(verify_generation())
