import asyncio
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.sub_agents.trend_analysis_agent.trend_analysis_agent import generate_trend_snapshot

async def verify_trends():
    print("--- Verifying Trend Analysis Agent ---")
    
    # Run analysis
    snapshot = await generate_trend_snapshot(2010, 2025)
    
    print(f"\nSnapshot Created: {snapshot.id}")
    print(f"Year Range: {snapshot.year_range}")
    
    stats = snapshot.topic_stats_json
    print(f"\nTotal Topics Analyzed: {len(stats)}")
    
    print("\n--- Top 5 Emerging Topics ---")
    emerging = [t for t in stats.values() if isinstance(t, dict) and t.get('status') == 'emerging']
    emerging.sort(key=lambda x: x['trend_slope'], reverse=True)
    
    for t in emerging[:5]:
        print(f"Topic: {t['name']}")
        print(f"  Slope: {t['trend_slope']}")
        print(f"  Freq: {t['frequency_by_year']}")
        print(f"  Taxonomy: {t.get('taxonomy_distribution', 'N/A')}")
        print("-" * 20)
        
    print("\n--- Top 5 High Gap Topics (Due for recurrence) ---")
    gap_topics = [t for t in stats.values() if isinstance(t, dict) and t.get('gap_score', 0) > 0]
    gap_topics.sort(key=lambda x: x['gap_score'], reverse=True)
    
    for t in gap_topics[:5]:
        print(f"Topic: {t['name']}")
        print(f"  Gap Score: {t['gap_score']}")
        print(f"  Last Asked: {t['last_asked_year']}")
        print("-" * 20)

    print("\n--- Qualitative Insight (LLM) ---")
    meta = stats.get("_meta", {})
    print(meta.get("qualitative_insight", "No insight generated."))

if __name__ == "__main__":
    asyncio.run(verify_trends())
