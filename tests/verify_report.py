import asyncio
from sqlalchemy import select
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import get_session
from src.data_models.models import TrendSnapshot
from src.sub_agents.report_writer_agent.report_writer import generate_comprehensive_report
from utils.pdf_generator import markdown_to_pdf

async def verify_report():
    print("--- Verifying Report Generation ---")
    
    snapshot_id = None
    async for session in get_session():
        stmt = select(TrendSnapshot).order_by(TrendSnapshot.created_at.desc()).limit(1)
        result = await session.execute(stmt)
        snapshot = result.scalar_one_or_none()
        if snapshot:
            snapshot_id = snapshot.id
        break
    
    if snapshot_id:
        print(f"Generating report for Snapshot: {snapshot_id}")
        await generate_comprehensive_report(snapshot_id)
        print("Report generated.")
        
        # Also convert the existing paper markdown to PDF
        try:
            with open("generated_paper.md", "r", encoding="utf-8") as f:
                paper_md = f.read()
            markdown_to_pdf(paper_md, "generated_paper.pdf", title="Predicted Exam 2025")
            print("Paper PDF generated.")
        except Exception as e:
            print(f"Could not generate paper PDF: {e}")
            
    else:
        print("No snapshot found.")

if __name__ == "__main__":
    asyncio.run(verify_report())
