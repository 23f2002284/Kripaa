import asyncio
from sqlalchemy import select
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import get_session
from src.data_models.models import TrendSnapshot, CandidateStatus
from src.sub_agents.voting_ranking_agent.voting_agent import run_voting_process

async def verify_voting():
    print("--- Verifying Voting/Ranking Agent ---")
    
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
        print("No snapshot found.")
        return

    # 2. Run Voting
    selected = await run_voting_process(snapshot_id, target_count=20)
    
    print(f"\nSelected {len(selected)} candidates.")
    
    # 3. Inspect Selection
    print("\n--- Selected Candidates ---")
    for c in selected[:10]:
        print(f"ID: {c.id}")
        print(f"Origin: {c.scores_json.get('origin')} ({c.scores_json.get('strategy')})")
        print(f"Relevance: {c.scores_json.get('relevance_score')}")
        print(f"Final Score: {c.scores_json.get('final_score')}")
        print("-" * 20)
        
    # Check Exclusions
    # We need to fetch excluded ones to see reasons
    from src.data_models.models import PredictionCandidate
    async for session in get_session():
        stmt = select(PredictionCandidate).where(
            PredictionCandidate.trend_snapshot_id == snapshot_id,
            PredictionCandidate.status == CandidateStatus.excluded
        )
        result = await session.execute(stmt)
        excluded = result.scalars().all()
        
        print(f"\nExcluded Candidates: {len(excluded)}")
        if excluded:
            print("Sample Exclusion Reasons:")
            for c in excluded[:10]:
                reason = c.scores_json.get('exclusion_reason', 'None')
                origin = c.scores_json.get('origin', 'unknown')
                relevance = c.scores_json.get('relevance_score', 0.0)
                print(f"  {origin}: {reason} (Rel: {relevance})")
        break

if __name__ == "__main__":
    asyncio.run(verify_voting())
