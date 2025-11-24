"""Normalization node."""
import asyncio
from utils.logger import get_logger
from src.schemas import PipelineState
from src.sub_agents.question_preprocessing_agent.question_preprocessing_agent import process_questions

logger = get_logger()

async def normalization_node(state: PipelineState) -> PipelineState:
    """Normalize all raw questions."""
    logger.info("=== Step 3: Question Normalization ===")
    state["current_step"] = "Normalization"
    
    try:
        await process_questions()
        logger.info("✓ Normalization complete")
    except Exception as e:
        logger.error(f"Error in normalization: {e}")
        state["errors"].append(f"Normalization: {str(e)}")
    
    return state
