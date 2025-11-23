import asyncio
from sqlalchemy import select
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import get_session
from src.data_models.models import TrendSnapshot
from src.sub_agents.sample_paper_generator.sample_paper_generator import generate_sample_paper

async def verify_paper():
    print("--- Verifying Sample Paper Generator ---")
    
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

    # 2. Generate Paper
    md_content, paper_id = await generate_sample_paper(snapshot_id, title="Predicted Exam Paper 2025")
    
    print(f"\nGenerated Paper ID: {paper_id}")
    print("\n--- Paper Content ---\n")
    print(md_content)
    
    # 3. Save to file for easy viewing
    with open("generated_paper.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    print("\nSaved to generated_paper.md")

if __name__ == "__main__":
    asyncio.run(verify_paper())
