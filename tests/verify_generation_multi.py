import asyncio
import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy import select
from utils.db import get_session
from src.data_models.models import TrendSnapshot
from src.sub_agents.question_generator_agent.question_generator_agent import generate_candidates_multi_section

async def verify_multi_temp_generation():
    print("--- Verifying Multi-Temperature Question Generation ---\n")
    
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

    # Generate candidates
    print("Generating candidates for all sections...")
    print("This will generate:")
    print("  - Section A: 30 candidates (2 marks)")
    print("  - Section B: 36 candidates (5 marks)")
    print("  - Section C: 15 candidates (10 marks)")
    print("  - Total: 81 candidates\n")
    print("Using temperatures: 0.2 (conservative), 0.5 (balanced), 0.9 (creative)")
    print("Model: gemini-2.5-pro\n")
    
    results = await generate_candidates_multi_section(snapshot_id, 2025)
    
    print("\n--- Generation Complete ---\n")
    for section, candidates in results.items():
        print(f"Section {section}: {len(candidates)} candidates generated")
        
        # Show distribution by origin
        origins = {}
        temps = {}
        for c in candidates:
            origin = c.scores_json.get("origin", "unknown")
            temp = c.scores_json.get("llm_temperature", 0)
            origins[origin] = origins.get(origin, 0) + 1
            temps[temp] = temps.get(temp, 0) + 1
        
        print(f"  Origins: {origins}")
        print(f"  Temps: {temps}\n")

if __name__ == "__main__":
    asyncio.run(verify_multi_temp_generation())
