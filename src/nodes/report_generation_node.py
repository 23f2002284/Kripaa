"""Report generation node."""
import asyncio
from pathlib import Path
from utils.logger import get_logger
from src.schemas import PipelineState
from src.sub_agents.report_writer_agent.report_writer import generate_comprehensive_report

logger = get_logger()

async def report_generation_node(state: PipelineState) -> PipelineState:
    """Generate comprehensive report."""
    logger.info("=== Step 10: Comprehensive Report Generation ===")
    state["current_step"] = "Report Generation"
    
    try:
        if not state["snapshot_id"]:
            raise ValueError("No snapshot ID available")
        
        # Create output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Pass output directory to report writer
        await generate_comprehensive_report(state["snapshot_id"], str(output_dir))
        logger.info("✓ Comprehensive report generated")
        logger.info(f"  - {output_dir / 'comprehensive_report.md'}")
        logger.info(f"  - {output_dir / 'comprehensive_report.pdf'}")
        
        state["completed"] = True
    except Exception as e:
        logger.error(f"Error in report generation: {e}")
        state["errors"].append(f"Report Generation: {str(e)}")
    
    return state
