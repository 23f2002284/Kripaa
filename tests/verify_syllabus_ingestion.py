import asyncio
import os
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sub_agents.ocr_agent.ocr_agent import extract_syllabus_from_pdf, populate_syllabus_db
from src.data_models.models import SyllabusNode
from utils.db import get_session, init_db

async def verify_syllabus_ingestion(pdf_path: str):
    # 1. Define PDF path
    if not os.path.exists(pdf_path):
        print(f"Error: Syllabus PDF not found at {pdf_path}")
        return

    print(f"Testing syllabus ingestion with: {pdf_path}")

    # 2. Initialize DB (ensure tables exist)
    await init_db()

    # 3. Run Extraction
    print("Extracting syllabus topics...")
    try:
        topics = await extract_syllabus_from_pdf(pdf_path)
        print(f"Extracted {len(topics)} topics.")
        for topic in topics:
            print(f" - {topic.name} (Level {topic.level}, Parent: {topic.parent_name})")
    except Exception as e:
        print(f"Extraction failed: {e}")
        return

    if not topics:
        print("No topics extracted. Exiting.")
        return

    # 4. Populate DB
    print("Populating database...")
    try:
        await populate_syllabus_db(topics)
        print("Database populated.")
    except Exception as e:
        print(f"Population failed: {e}")
        return

    # 5. Verify Data in DB
    print("Verifying data in database...")
    async for session in get_session():
        result = await session.execute(select(SyllabusNode))
        db_nodes = result.scalars().all()
        print(f"Found {len(db_nodes)} syllabus nodes in DB.")
        
        # Check hierarchy
        for node in db_nodes:
            print(f" [DB] Topic: {node.topic} | Module: {node.module} | Parent Topic: {node.parent_topic} | Level: {node.level}")
            if node.description:
                print(f"      Desc: {node.description[:100]}...")
        break

if __name__ == "__main__":
    pdf_path = os.path.join("static", "syllabus", "CSPC3002.docx.pdf")
    asyncio.run(verify_syllabus_ingestion(pdf_path))
