import asyncio
from typing import List, Dict, Any, Tuple
from uuid import UUID
from collections import defaultdict
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from utils.db import get_session
from utils.logger import get_logger
from src.data_models.models import (
    QuestionNormalized, 
    QuestionRaw, 
    VariantGroup, 
    SyllabusNode, 
    TrendSnapshot,
    TopicStatus
)

logger = get_logger()

async def generate_trend_snapshot(start_year: int, end_year: int) -> TrendSnapshot:
    """
    Analyzes question data to generate a TrendSnapshot with topic stats.
    """
    logger.info(f"Starting Trend Analysis for {start_year}-{end_year}...")
    
    async for session in get_session():
        try:
            # 1. Fetch all QuestionNormalized with hierarchy
            # We need VariantGroup -> SyllabusNode to attribute questions to topics
            stmt = select(QuestionNormalized).options(
                selectinload(QuestionNormalized.variant_group).selectinload(VariantGroup.syllabus_node)
            )
            result = await session.execute(stmt)
            norm_questions = result.scalars().all()
            
            # 2. Build a lookup for QuestionRaw years
            # We need to know the year for each original_id to place it on the timeline
            stmt_raw = select(QuestionRaw.id, QuestionRaw.year)
            result_raw = await session.execute(stmt_raw)
            raw_year_map = {str(row[0]): row[1] for row in result_raw.all()}
            
            # 3. Aggregate Data
            # Structure: topic_id -> { year -> [list of questions] }
            topic_year_data = defaultdict(lambda: defaultdict(list))
            topic_info = {} # topic_id -> {name, module}
            
            for q in norm_questions:
                if not q.variant_group or not q.variant_group.syllabus_node:
                    continue
                
                topic = q.variant_group.syllabus_node
                topic_id = str(topic.id)
                topic_info[topic_id] = {
                    "topic": topic.topic, 
                    "module": topic.module,
                    "weight": topic.weight
                }
                
                # For each occurrence (original_id), record the year
                for raw_id in q.original_ids:
                    year = raw_year_map.get(str(raw_id))
                    if year and start_year <= year <= end_year:
                        topic_year_data[topic_id][year].append(q)

            # 4. Calculate Statistics
            topic_stats = {}
            emerging_topics = []
            declining_topics = []
            
            for topic_id, year_data in topic_year_data.items():
                years = sorted(year_data.keys())
                if not years:
                    continue
                
                # Frequency per year
                freq_map = {y: len(year_data[y]) for y in years}
                total_count = sum(freq_map.values())
                
                # Difficulty per year (avg of questions in that year)
                diff_map = {}
                for y, q_list in year_data.items():
                    diffs = [q.difficulty for q in q_list if q.difficulty is not None]
                    if diffs:
                        diff_map[y] = round(sum(diffs) / len(diffs), 2)
                
                # Calculate Trend Slope (Simple Linear Regression on Frequency)
                # We focus on the last 3-5 years for "Emerging" status if possible, else all available
                recent_years = [y for y in years if y >= end_year - 4]
                if len(recent_years) >= 2:
                    xs = np.array(recent_years)
                    ys = np.array([freq_map[y] for y in recent_years])
                    slope, _ = np.polyfit(xs, ys, 1)
                else:
                    slope = 0.0
                
                # Determine Status
                status = "stable"
                if slope > 0.5:
                    status = "emerging"
                    emerging_topics.append(topic_id)
                elif slope < -0.5:
                    status = "declining"
                    declining_topics.append(topic_id)
                
                # Gap Score Analysis
                last_asked = max(years)
                gap_years = end_year - last_asked
                # Default weight is 1.0 if not set. We can fetch it from topic_info if we added it there, 
                # but for now let's assume 1.0 or fetch it. 
                # actually topic_info only has name/module. Let's add weight to topic_info in step 3.
                topic_weight = topic_info[topic_id].get("weight", 1.0) 
                gap_score = gap_years * topic_weight if gap_years > 0 else 0
                
                # Taxonomy Evolution
                # year -> {level: count}
                taxonomy_map = defaultdict(lambda: defaultdict(int))
                for y, q_list in year_data.items():
                    for q in q_list:
                        for tax in q.taxonomy:
                            taxonomy_map[y][tax] += 1
                
                # Convert to percentage for the snapshot
                taxonomy_dist = {}
                for y, counts in taxonomy_map.items():
                    total_tax = sum(counts.values())
                    if total_tax > 0:
                        taxonomy_dist[y] = {k: round(v / total_tax, 2) for k, v in counts.items()}

                topic_stats[topic_id] = {
                    "name": topic_info[topic_id]["topic"],
                    "module": topic_info[topic_id]["module"],
                    "total_count": total_count,
                    "frequency_by_year": freq_map,
                    "difficulty_by_year": diff_map,
                    "taxonomy_distribution": taxonomy_dist,
                    "last_asked_year": last_asked,
                    "gap_score": gap_score,
                    "trend_slope": round(slope, 2),
                    "status": status
                }

            # 5. Generate Qualitative Insight using LLM
            # Prepare data for prompt
            emerging_names = [topic_stats[tid]["name"] for tid in emerging_topics]
            declining_names = [topic_stats[tid]["name"] for tid in declining_topics]
            
            # Find high gap topics (top 5 by gap score)
            gap_list = sorted(topic_stats.items(), key=lambda x: x[1]["gap_score"], reverse=True)[:5]
            gap_names = [f"{v['name']} (Gap: {v['gap_score']})" for k, v in gap_list if v['gap_score'] > 0]
            
            # Summarize taxonomy shifts (simplified for prompt)
            # We can just pass a few examples or a general note. Let's pass the global distribution change if possible, 
            # or just list topics with significant shifts. For now, let's list top 3 topics with high 'Analyze/Create' % in recent years.
            
            # Call LLM
            from utils.llm import get_llm
            from src.sub_agents.trend_analysis_agent.prompts import TREND_ANALYSIS_PROMPT
            
            llm = get_llm(temperature=0.2)
            chain = TREND_ANALYSIS_PROMPT | llm
            
            insight_response = await chain.ainvoke({
                "emerging_topics": ", ".join(emerging_names) if emerging_names else "None",
                "declining_topics": ", ".join(declining_names) if declining_names else "None",
                "gap_topics": ", ".join(gap_names) if gap_names else "None",
                "taxonomy_shifts": "See detailed stats in snapshot." # Placeholder for now to keep prompt simple
            })
            
            qualitative_insight = insight_response.content
            
            # 6. Create Snapshot
            snapshot = TrendSnapshot(
                year_range=[start_year, end_year],
                topic_stats_json=topic_stats,
                emerging_topics=emerging_topics,
                declining_topics=declining_topics,
                # We need to store the insight. The model definition for TrendSnapshot doesn't have an 'insight' field yet.
                # We should add it or store it in topic_stats_json for now. Let's add it to topic_stats_json as a special key.
            )
            # Hack: Store insight in the stats json for now to avoid schema change mid-flight if user didn't ask for it.
            # But wait, user approved "LLM Qualitative Insight". I should probably add a field or put it in the JSON.
            # Let's put it in the JSON under "_meta" to be safe.
            snapshot.topic_stats_json["_meta"] = {"qualitative_insight": qualitative_insight}
            
            session.add(snapshot)
            await session.commit()
            
            logger.info(f"Trend Analysis Complete. Snapshot ID: {snapshot.id}")
            logger.info(f"Identified {len(emerging_topics)} emerging and {len(declining_topics)} declining topics.")
            
            return snapshot

        except Exception as e:
            logger.error(f"Error in trend analysis: {e}")
            await session.rollback()
            raise
        break

if __name__ == "__main__":
    # Default run for testing
    asyncio.run(generate_trend_snapshot(2015, 2024))
