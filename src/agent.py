"""
Main orchestration agent using LangGraph.
Coordinates the complete exam generation pipeline.
"""
import asyncio
from pathlib import Path
from langgraph.graph import StateGraph, END
from utils.logger import get_logger
from src.schemas import PipelineState
from src.nodes import (
    ocr_pyqs_node,
    ocr_syllabus_node,
    normalization_node,
    variant_detection_node,
    syllabus_mapping_node,
    trend_analysis_node,
    question_generation_node,
    voting_node,
    paper_generation_node,
    report_generation_node
)

logger = get_logger()

def create_pipeline() -> StateGraph:
    """Create the LangGraph pipeline."""
    workflow = StateGraph(PipelineState)
    
    # Add nodes
    workflow.add_node("ocr_pyqs", ocr_pyqs_node)
    workflow.add_node("ocr_syllabus", ocr_syllabus_node)
    workflow.add_node("normalization", normalization_node)
    workflow.add_node("variant_detection", variant_detection_node)
    workflow.add_node("syllabus_mapping", syllabus_mapping_node)
    workflow.add_node("trend_analysis", trend_analysis_node)
    workflow.add_node("question_generation", question_generation_node)
    workflow.add_node("voting", voting_node)
    workflow.add_node("paper_generation", paper_generation_node)
    workflow.add_node("report_generation", report_generation_node)
    
    # Define edges (sequential flow)
    workflow.set_entry_point("ocr_pyqs")
    workflow.add_edge("ocr_pyqs", "ocr_syllabus")
    workflow.add_edge("ocr_syllabus", "normalization")
    workflow.add_edge("normalization", "variant_detection")
    workflow.add_edge("variant_detection", "syllabus_mapping")
    workflow.add_edge("syllabus_mapping", "trend_analysis")
    workflow.add_edge("trend_analysis", "question_generation")
    workflow.add_edge("question_generation", "voting")
    workflow.add_edge("voting", "paper_generation")
    workflow.add_edge("paper_generation", "report_generation")
    workflow.add_edge("report_generation", END)
    
    return workflow.compile()

async def run_pipeline(target_year: int = 2025):
    """Run the complete exam generation pipeline."""
    logger.info("=" * 60)
    logger.info("KRIPAA - Automated Exam Generation Pipeline")
    logger.info("=" * 60)
    
    # Get project root (parent of src/)
    project_root = Path(__file__).parent.parent
    
    # Initialize state
    initial_state: PipelineState = {
        "target_year": target_year,
        "pyq_directory": str(project_root / "static" / "pyqs"),
        "syllabus_directory": str(project_root / "static" / "syllabus"),
        "snapshot_id": None,
        "paper_markdown": None,
        "current_step": "Initializing",
        "errors": [],
        "completed": False
    }
    
    # Create and run pipeline
    app = create_pipeline()
    final_state = app.invoke(initial_state)
"""
Main orchestration agent using LangGraph.
Coordinates the complete exam generation pipeline.
"""
import asyncio
from pathlib import Path
from langgraph.graph import StateGraph, END
from utils.logger import get_logger
from src.schemas import PipelineState
from src.nodes import (
    ocr_pyqs_node,
    ocr_syllabus_node,
    normalization_node,
    variant_detection_node,
    syllabus_mapping_node,
    trend_analysis_node,
    question_generation_node,
    voting_node,
    paper_generation_node,
    report_generation_node
)

logger = get_logger()

def create_pipeline() -> StateGraph:
    """Create the LangGraph pipeline."""
    workflow = StateGraph(PipelineState)
    
    # Add nodes
    workflow.add_node("ocr_pyqs", ocr_pyqs_node)
    workflow.add_node("ocr_syllabus", ocr_syllabus_node)
    workflow.add_node("normalization", normalization_node)
    workflow.add_node("variant_detection", variant_detection_node)
    workflow.add_node("syllabus_mapping", syllabus_mapping_node)
    workflow.add_node("trend_analysis", trend_analysis_node)
    workflow.add_node("question_generation", question_generation_node)
    workflow.add_node("voting", voting_node)
    workflow.add_node("paper_generation", paper_generation_node)
    workflow.add_node("report_generation", report_generation_node)
    
    # Define edges (sequential flow)
    workflow.set_entry_point("ocr_pyqs")
    workflow.add_edge("ocr_pyqs", "ocr_syllabus")
    workflow.add_edge("ocr_syllabus", "normalization")
    workflow.add_edge("normalization", "variant_detection")
    workflow.add_edge("variant_detection", "syllabus_mapping")
    workflow.add_edge("syllabus_mapping", "trend_analysis")
    workflow.add_edge("trend_analysis", "question_generation")
    workflow.add_edge("question_generation", "voting")
    workflow.add_edge("voting", "paper_generation")
    workflow.add_edge("paper_generation", "report_generation")
    workflow.add_edge("report_generation", END)
    
    return workflow.compile()

async def run_pipeline(target_year: int = 2025):
    """Run the complete exam generation pipeline."""
    logger.info("=" * 60)
    logger.info("KRIPAA - Automated Exam Generation Pipeline")
    logger.info("=" * 60)
    
    # Get project root (parent of src/)
    project_root = Path(__file__).parent.parent
    
    # Initialize state
    initial_state: PipelineState = {
        "target_year": target_year,
        "pyq_directory": str(project_root / "static" / "pyqs"),
        "syllabus_directory": str(project_root / "static" / "syllabus"),
        "snapshot_id": None,
        "paper_markdown": None,
        "current_step": "Initializing",
        "errors": [],
        "completed": False
    }
    
    # Create and run pipeline
    app = create_pipeline()
    final_state = await app.ainvoke(initial_state)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 60)
    
    if final_state["completed"] and not final_state["errors"]:
        logger.info("✓ All steps completed successfully!")
        logger.info(f"✓ Generated paper: output/generated_paper.pdf")
        logger.info(f"✓ Comprehensive report: output/comprehensive_report.pdf")
    else:
        logger.warning(f"⚠ Completed with {len(final_state['errors'])} errors:")
        for error in final_state["errors"]:
            logger.warning(f"  - {error}")
    
    return final_state