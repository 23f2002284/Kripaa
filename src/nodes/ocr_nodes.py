"""OCR nodes for processing PDFs."""
import asyncio
from pathlib import Path
from utils.logger import get_logger
from src.schemas import PipelineState
from src.sub_agents.ocr_agent.ocr_agent import (
    extract_questions_from_pdf,
    populate_db,
    extract_syllabus_from_pdf,
    populate_syllabus_db
)

logger = get_logger()

async def ocr_pyqs_node(state: PipelineState) -> PipelineState:
    """Process all PYQ PDFs with OCR."""
    logger.info("=== Step 1: OCR Processing (PYQs) ===")
    state["current_step"] = "OCR (PYQs)"
    
    try:
        pyq_dir = Path(state["pyq_directory"])
        pdf_files = list(pyq_dir.glob("*.pdf"))
        
        logger.info(f"Found {len(pdf_files)} PYQ PDF files")
        
        async def process_pyq(pdf_path):
            questions = await extract_questions_from_pdf(str(pdf_path))
            if questions:
                await populate_db(questions)
        
        for pdf_path in pdf_files:
            logger.info(f"Processing: {pdf_path.name}")
            await process_pyq(pdf_path)
        
        logger.info("PYQ OCR complete")
    except Exception as e:
        logger.error(f"Error in OCR (PYQs): {e}")
        state["errors"].append(f"OCR PYQs: {str(e)}")
    
    return state

async def ocr_syllabus_node(state: PipelineState) -> PipelineState:
    """Process syllabus PDF with OCR."""
    logger.info("=== Step 2: OCR Processing (Syllabus) ===")
    state["current_step"] = "OCR (Syllabus)"
    
    try:
        syll_dir = Path(state["syllabus_directory"])
        syllabus_pdf = next(syll_dir.glob("*.pdf"), None)
        
        async def process_syllabus(pdf_path):
            topics = await extract_syllabus_from_pdf(str(pdf_path))
            if topics:
                await populate_syllabus_db(topics)
        
        if syllabus_pdf:
            logger.info(f"Processing syllabus: {syllabus_pdf.name}")
            await process_syllabus(syllabus_pdf)
            logger.info("Syllabus OCR complete")
        else:
            logger.warning("No syllabus PDF found")
            state["errors"].append("No syllabus PDF found")
    
    except Exception as e:
        logger.error(f"Error in OCR (Syllabus): {e}")
        state["errors"].append(f"OCR Syllabus: {str(e)}")
    
    return state
