import asyncio
import sys
import os
import json
sys.path.append(os.getcwd())
from src.sub_agents.trend_analysis_agent.trend_analysis_agent import generate_trend_snapshot

async def verify_enhanced_trends():
    print("--- Verifying Enhanced Trend Analysis ---\n")
    print("Generating trend snapshot with section-aware tracking and cyclicity detection...\n")
    
    # Generate snapshot
    snapshot = await generate_trend_snapshot(2015, 2024)
    
    print(f"Snapshot ID: {snapshot.id}")
    print(f"Year Range: {snapshot.year_range[0]}-{snapshot.year_range[1]}\n")
    print(f"Emerging Topics: {len(snapshot.emerging_topics)}")
    print(f"Declining Topics: {len(snapshot.declining_topics)}\n")
    
    # Show sample topics with enhancements
    print("=== SAMPLE TOPICS WITH ENHANCEMENTS ===\n")
    
    topic_stats = snapshot.topic_stats_json
    sample_topics = list(topic_stats.items())[:5]  # First 5 topics
    
    for topic_id, data in sample_topics:
        if topic_id == "_meta":
            continue
            
        print(f"Topic: {data.get('name', 'Unknown')}")
        print(f"  Module: {data.get('module', 'Unknown')}")
        print(f"  Status: {data.get('status', 'stable')}")
        print(f"  Gap Score: {data.get('gap_score', 0)}")
        
        # Section Distribution (NEW)
        section_dist = data.get('section_distribution', {})
        section_pref = data.get('section_preference', 'Unknown')
        print(f"  Section Distribution: A={section_dist.get('A', 0):.0%}, B={section_dist.get('B', 0):.0%}, C={section_dist.get('C', 0):.0%}")
        print(f"  Section Preference: {section_pref}")
        print(f"  Avg Difficulty: {data.get('avg_difficulty', 0)}")
        
        # Cyclicity (NEW)
        cyclicity = data.get('cyclicity', {})
        pattern = cyclicity.get('pattern_type', 'unknown')
        confidence = cyclicity.get('confidence', 0)
        print(f"  Cyclicity Pattern: {pattern}")
        
        if pattern == 'regular':
            cycle = cyclicity.get('cycle_length')
            next_year = cyclicity.get('next_expected_year')
            print(f"    - Appears every {cycle} years")
            print(f"    - Next expected: {next_year}")
        elif pattern in ['odd_years', 'even_years']:
            next_year = cyclicity.get('next_expected_year')
            print(f"    - Next expected: {next_year}")
        elif pattern == 'mostly_regular':
            cycle = cyclicity.get('cycle_length')
            print(f"    - Usually every {cycle} years")
        
        print(f"    - Confidence: {confidence:.0%}")
        print()
    
    # Show LLM insight
    meta = topic_stats.get('_meta', {})
    insight = meta.get('qualitative_insight', 'No insight available')
    print("=== LLM QUALITATIVE INSIGHT ===")
    print(insight)
    print()
    
    print("Verification Complete!")
    print(f"\nEnhanced data is now stored in Snapshot {snapshot.id}")
    print("This will help the generator target appropriate topics per section.")

if __name__ == "__main__":
    asyncio.run(verify_enhanced_trends())
