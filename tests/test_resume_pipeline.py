import asyncio
from uuid import UUID
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.schemas import PipelineState
from src.nodes import (
    syllabus_mapping_node,
    trend_analysis_node,
    question_generation_node,
    voting_node,
    paper_generation_node,
    report_generation_node
)
from utils.logger import get_logger

logger = get_logger()

async def resume_pipeline():
    # Snapshot ID from the previous run log
    snapshot_id = UUID("7ab325cc-e809-4b31-ba3a-9f22b97e3195")
    target_year = 2025
    
    state: PipelineState = {
        "target_year": target_year,
        "snapshot_id": snapshot_id,
        "current_step": "Resuming",
        "errors": [],
        "completed": False,
        "pyq_directory": "", 
        "syllabus_directory": "",
        "paper_markdown": None
    }
    
    logger.info(f"Resuming pipeline from Syllabus Mapping with Snapshot ID: {snapshot_id}")
    
    try:
        # Step 5: Syllabus Mapping (Enrichment + Mapping)
        logger.info("Running Syllabus Mapping Node...")
        state = await syllabus_mapping_node(state)

        # Step 6: Trend Analysis
        logger.info("Running Trend Analysis Node...")
        state = await trend_analysis_node(state)

        # Step 7: Question Generation
        logger.info("Running Question Generation Node...")
        state = await question_generation_node(state)
        
        # Step 8: Voting
        logger.info("Running Voting Node...")
        state = await voting_node(state)
        
        # Step 9: Paper Generation
        logger.info("Running Paper Generation Node...")
        state = await paper_generation_node(state)
        
        # Step 10: Report Generation
        logger.info("Running Report Generation Node...")
        state = await report_generation_node(state)
        
        if not state["errors"]:
            logger.info("✅ Resumed pipeline completed successfully!")
        else:
            logger.error(f"❌ Resumed pipeline completed with errors: {state['errors']}")
        
    except Exception as e:
        logger.error(f"Pipeline resumption failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(resume_pipeline())
