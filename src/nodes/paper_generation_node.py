"""Paper generation node."""
import asyncio
from pathlib import Path
from utils.logger import get_logger
from src.schemas import PipelineState
from src.sub_agents.sample_paper_generator.sample_paper_generator import generate_sample_paper
from utils.simple_pdf_generator import generate_simple_exam_pdf

logger = get_logger()

async def paper_generation_node(state: PipelineState) -> PipelineState:
    """Generate sample paper."""
    logger.info("=== Step 9: Sample Paper Generation ===")
    state["current_step"] = "Paper Generation"
    
    try:
        if not state["snapshot_id"]:
            raise ValueError("No snapshot ID available")
        
        # Create output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        markdown, paper_id = await generate_sample_paper(
            state["snapshot_id"],
            f"Predicted Exam {state['target_year']}"
        )
        
        # Save markdown
        md_path = output_dir / "generated_paper.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        
        # Generate PDF
        pdf_path = output_dir / "generated_paper.pdf"
        generate_simple_exam_pdf(str(md_path), str(pdf_path))
        
        state["paper_markdown"] = markdown
        logger.info(f"✓ Sample paper generated (Paper ID: {paper_id})")
        logger.info(f"  - {md_path}")
        logger.info(f"  - {pdf_path}")
    except Exception as e:
        logger.error(f"Error in paper generation: {e}")
        state["errors"].append(f"Paper Generation: {str(e)}")
    
    return state
