"""Variant detection node."""
import asyncio
from utils.logger import get_logger
from src.schemas import PipelineState
from src.sub_agents.question_preprocessing_agent.variant_grouping import process_grouping

logger = get_logger()

async def variant_detection_node(state: PipelineState) -> PipelineState:
    """Detect question variants."""
    logger.info("=== Step 4: Variant Detection ===")
    state["current_step"] = "Variant Detection"
    
    try:
        await process_grouping()
        logger.info("✓ Variant detection complete")
    except Exception as e:
        logger.error(f"Error in variant detection: {e}")
        state["errors"].append(f"Variant Detection: {str(e)}")
    
    return state
