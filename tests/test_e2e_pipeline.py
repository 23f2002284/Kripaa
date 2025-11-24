"""
End-to-end pipeline test
Tests the complete LangGraph orchestration from start to finish.
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.append(os.getcwd())

from src.agent import run_pipeline
from utils.logger import get_logger

logger = get_logger()

async def test_full_pipeline():
    """Test the complete pipeline end-to-end."""
    
    print("=" * 70)
    print("KRIPAA - END-TO-END PIPELINE TEST")
    print("=" * 70)
    print()
    
    # Pre-flight checks
    print("📋 PRE-FLIGHT CHECKS")
    print()
    
    # Check 1: Static folders
    pyq_dir = Path("static/pyqs")
    syllabus_dir = Path("static/syllabus")
    
    if not pyq_dir.exists():
        print("❌ ERROR: static/pyqs/ directory not found")
        print("   Create it and add PYQ PDFs")
        return False
    
    if not syllabus_dir.exists():
        print("❌ ERROR: static/syllabus/ directory not found")
        print("   Create it and add syllabus PDF")
        return False
    
    pyq_pdfs = list(pyq_dir.glob("*.pdf"))
    syllabus_pdfs = list(syllabus_dir.glob("*.pdf"))
    
    print(f"✓ Found {len(pyq_pdfs)} PYQ PDFs")
    print(f"✓ Found {len(syllabus_pdfs)} syllabus PDFs")
    print()
    
    if len(pyq_pdfs) == 0:
        print("❌ ERROR: No PYQ PDFs found in static/pyqs/")
        return False
    
    if len(syllabus_pdfs) == 0:
        print("⚠️  WARNING: No syllabus PDF found in static/syllabus/")
    
    # Check 2: Database connection
    try:
        from utils.db import get_session
        async for session in get_session():
            print("✓ Database connection successful")
            break
    except Exception as e:
        print(f"❌ ERROR: Database connection failed: {e}")
        return False
    
    print()
    
    # Check 3: Environment variables
    import os
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERROR: GOOGLE_API_KEY not set in environment")
        return False
    
    print("✓ GOOGLE_API_KEY found")
    print()
    
    print("=" * 70)
    print("STARTING PIPELINE")
    print("=" * 70)
    print()
    
    # Run the pipeline
    try:
        final_state = await run_pipeline(target_year=2025)
        
        print()
        print("=" * 70)
        print("TEST RESULTS")
        print("=" * 70)
        print()
        
        if final_state["completed"]:
            print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
            print()
            
            # Check outputs
            output_dir = Path("output")
            paper_pdf = output_dir / "generated_paper.pdf"
            report_pdf = output_dir / "comprehensive_report.pdf"
            
            if paper_pdf.exists():
                size = paper_pdf.stat().st_size / 1024  # KB
                print(f"✓ Generated paper: {paper_pdf} ({size:.1f} KB)")
            else:
                print(f"⚠️  Paper PDF not found: {paper_pdf}")
            
            if report_pdf.exists():
                size = report_pdf.stat().st_size / 1024  # KB
                print(f"✓ Comprehensive report: {report_pdf} ({size:.1f} KB)")
            else:
                print(f"⚠️  Report PDF not found: {report_pdf}")
            
            print()
            
            if final_state["errors"]:
                print(f"⚠️  Completed with {len(final_state['errors'])} warnings:")
                for error in final_state["errors"]:
                    print(f"  - {error}")
            else:
                print("✓ No errors encountered")
            
            return True
        else:
            print("❌ PIPELINE FAILED")
            print()
            print(f"Errors ({len(final_state['errors'])}):")
            for error in final_state["errors"]:
                print(f"  - {error}")
            return False
            
    except Exception as e:
        print(f"❌ PIPELINE CRASHED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_full_pipeline())
    sys.exit(0 if success else 1)