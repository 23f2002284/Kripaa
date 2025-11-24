"""Trend analysis node."""
import asyncio
from utils.logger import get_logger
from src.schemas import PipelineState
from src.sub_agents.trend_analysis_agent.trend_analysis_agent import generate_trend_snapshot

logger = get_logger()

async def trend_analysis_node(state: PipelineState) -> PipelineState:
    """Analyze trends with enhanced detection."""
    logger.info("=== Step 6: Enhanced Trend Analysis ===")
    state["current_step"] = "Trend Analysis"
    
    try:
        snapshot = await generate_trend_snapshot(2015, state["target_year"] - 1)
        state["snapshot_id"] = snapshot.id
        logger.info(f"✓ Trend analysis complete (Snapshot: {snapshot.id})")
    except Exception as e:
        logger.error(f"Error in trend analysis: {e}")
        state["errors"].append(f"Trend Analysis: {str(e)}")
    
    return state
