import sys
import os
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime
import pathlib
# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sub_agents.ocr_agent.ocr_agent import extract_questions_from_pdf, populate_db
from src.sub_agents.ocr_agent.schemas import ExtractionResult, ExtractedQuestion

async def test_single_pdf_extraction(pdf_path:str):
    """
    test single pdf extraction
    """
    questions = await extract_questions_from_pdf(pdf_path)
    print(f"Extracted {len(questions)} questions.")
    await populate_db(questions)

async def test_multiple_pdf_extraction(pdf_paths:pathlib.Path):
    """
    test multiple pdf extraction
    """
    for pdf_path in pdf_paths.glob("**/*.pdf"):
        await test_single_pdf_extraction(pdf_path)

if __name__ == "__main__":
    # pdf_path = pathlib.Path("static//pyqs")
    # asyncio.run(test_multiple_pdf_extraction(pdf_path))
    # print("exists") if os.path.exists(pdf_path) else print("does not exist")
    pdf_paths = [
        r"static\pyqs\OPERATING SYSTEMS-CSE,ELE,ETC,IT-5th-2021-22.pdf",
        r"static\pyqs\OPERATING SYSTEMS-HRB071-CSE-3BPE-19-20.pdf",
        # r"static\pyqs\OPERATING SYSTEMS - CSE -5th semistar Regular & Back Exam- 2018-19.pdf"
    ]
    async def main():
        for pdf_path in pdf_paths:
            await test_single_pdf_extraction(pdf_path)
    asyncio.run(main())
