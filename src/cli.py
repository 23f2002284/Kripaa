"""
Kripaa CLI - Main entry point for exam generation pipeline
"""
import argparse
import asyncio
from src.agent import run_pipeline
from utils.logger import get_logger

logger = get_logger()

def main():
    parser = argparse.ArgumentParser(
        description="Kripaa - Automated Exam Paper Generation System"
    )
    parser.add_argument(
        "--target-year",
        type=int,
        default=2025,
        help="Target year for exam prediction (default: 2025)"
    )
    
    args = parser.parse_args()
    
    logger.info("")
    logger.info(f"🎓 Generating exam paper for {args.target_year}...")
    logger.info(f"📁 Reading PYQs from: static/pyqs/")
    logger.info(f"📁 Reading syllabus from: static/syllabus/")
    logger.info("")
    
    asyncio.run(run_pipeline(args.target_year))

if __name__ == "__main__":
    main()
