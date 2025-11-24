"""Question generation node."""
import asyncio
from utils.logger import get_logger
from src.schemas import PipelineState
from src.sub_agents.question_generator_agent.question_generator_agent import generate_candidates_multi_section

logger = get_logger()

async def question_generation_node(state: PipelineState) -> PipelineState:
    """Generate questions with multi-temperature ensemble."""
    logger.info("=== Step 7: Multi-Temperature Question Generation ===")
    state["current_step"] = "Question Generation"
    
    try:
        if not state["snapshot_id"]:
            raise ValueError("No snapshot ID available")
        
        await generate_candidates_multi_section(
            state["snapshot_id"],
            state["target_year"]
        )
        logger.info("✓ Question generation complete (81 candidates)")
    except Exception as e:
        logger.error(f"Error in question generation: {e}")
        state["errors"].append(f"Question Generation: {str(e)}")
    
    return state
