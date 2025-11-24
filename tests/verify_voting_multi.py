import asyncio
import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy import select
from utils.db import get_session
from src.data_models.models import TrendSnapshot
from src.sub_agents.voting_ranking_agent.voting_agent import run_voting_process_multi_section

async def verify_multi_section_voting():
    print("--- Verifying Section-Aware Voting ---\n")
    
    snapshot_id = None
    async for session in get_session():
        stmt = select(TrendSnapshot).order_by(TrendSnapshot.created_at.desc()).limit(1)
        result = await session.execute(stmt)
        snapshot = result.scalar_one_or_none()
        if snapshot:
            snapshot_id = snapshot.id
            print(f"Using Snapshot ID: {snapshot_id}\n")
        break
    
    if not snapshot_id:
        print("No snapshot found.")
        return

    print("Running section-aware voting...")
    print("Target selection:")
    print("  - Section A: 10 questions (from ~30)")
    print("  - Section B: 12 questions (from ~36)")
    print("  - Section C: 5 questions (from ~15)")
    print("  - Total: 27 questions\n")
    
    results = await run_voting_process_multi_section(snapshot_id)
    
    print("\n--- Voting Complete ---\n")
    total_selected = 0
    for section, selected in results.items():
        print(f"Section {section}: {len(selected)} questions selected")
        total_selected += len(selected)
        
        # Show sample
        if selected:
            print(f"  Sample question: {selected[0].normalized_question.base_form[:80]}...")
            print(f"  Relevance: {selected[0].scores_json.get('relevance_score', 0):.3f}\n")
    
    print(f"Total Selected: {total_selected}")
    print(f"Total Marks: Section A: {len(results.get('A', []))*2}, B: {len(results.get('B', []))*5}, C: {len(results.get('C', []))*10}")
    total_marks = len(results.get('A', []))*2 + len(results.get('B', []))*5 + len(results.get('C', []))*10
    print(f"Grand Total: {total_marks} marks")

if __name__ == "__main__":
    asyncio.run(verify_multi_section_voting())
