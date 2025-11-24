"""Voting node."""
import asyncio
from utils.logger import get_logger
from src.schemas import PipelineState
from src.sub_agents.voting_ranking_agent.voting_agent import run_voting_process_multi_section

logger = get_logger()

async def voting_node(state: PipelineState) -> PipelineState:
    """Vote and select final questions."""
    logger.info("=== Step 8: Section-Aware Voting ===")
    state["current_step"] = "Voting & Selection"
    
    try:
        if not state["snapshot_id"]:
            raise ValueError("No snapshot ID available")
        
        await run_voting_process_multi_section(state["snapshot_id"])
        logger.info("✓ Voting complete (27 questions selected)")
    except Exception as e:
        logger.error(f"Error in voting: {e}")
        state["errors"].append(f"Voting: {str(e)}")
    
    return state
