"""Syllabus mapping node."""
import asyncio
from utils.logger import get_logger
from src.schemas import PipelineState
from src.sub_agents.syll_mapping_tag_agent.mapping_agent import (
    map_questions_to_syllabus,
    enrich_syllabus_nodes,
    enrich_variant_groups
)

logger = get_logger()

async def syllabus_mapping_node(state: PipelineState) -> PipelineState:
    """Map questions to syllabus."""
    logger.info("=== Step 5: Syllabus Mapping ===")
    state["current_step"] = "Syllabus Mapping"
    
    try:
        # 1. Enrich Syllabus Nodes (Generate Embeddings)
        await enrich_syllabus_nodes()
        
        # 2. Enrich Variant Groups (Generate Embeddings)
        await enrich_variant_groups()
        
        # 3. Map Questions
        await map_questions_to_syllabus()
        logger.info("✓ Syllabus mapping complete")
    except Exception as e:
        logger.error(f"Error in syllabus mapping: {e}")
        state["errors"].append(f"Syllabus Mapping: {str(e)}")
    
    return state
