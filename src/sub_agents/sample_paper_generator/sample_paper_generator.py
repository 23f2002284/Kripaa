import asyncio
from typing import List, Dict, Tuple
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from utils.db import get_session
from utils.logger import get_logger
from src.data_models.models import (
    PredictionCandidate,
    CandidateStatus,
    SamplePaper,
    SamplePaperItem,
    QuestionNormalized,
    TrendSnapshot
)

logger = get_logger()

async def generate_sample_paper(snapshot_id: UUID, title: str = "Generated Sample Paper") -> Tuple[str, UUID]:
    """
    Generates a sample paper from selected candidates.
    Returns: (Markdown Content, SamplePaper ID)
    """
    logger.info(f"Generating Sample Paper for Snapshot {snapshot_id}...")
    
    async for session in get_session():
        try:
            # 1. Fetch Selected Candidates
            stmt = select(PredictionCandidate).options(
                selectinload(PredictionCandidate.normalized_question)
            ).where(
                PredictionCandidate.trend_snapshot_id == snapshot_id,
                PredictionCandidate.status == CandidateStatus.selected
            )
            
            result = await session.execute(stmt)
            candidates = result.scalars().all()
            
            if not candidates:
                logger.warning("No selected candidates found.")
                return "No candidates selected.", None

            # 2. Assign Sections & Marks
            # Strategy:
            # Diff 1-2 -> Section A (2 marks)
            # Diff 3   -> Section B (5 marks)
            # Diff 4-5 -> Section C (10 marks)
            
            sections = {
                "A": [],
                "B": [],
                "C": []
            }
            
            items_to_create = []
            total_marks = 0
            
            # Sort by difficulty to help with sectioning if needed, but we iterate
            sorted_candidates = sorted(candidates, key=lambda c: c.normalized_question.difficulty or 3)
            
            for i, cand in enumerate(sorted_candidates):
                q = cand.normalized_question
                diff = q.difficulty if q.difficulty else 3
                
                if diff <= 2:
                    sec = "A"
                    marks = 2
                elif diff == 3:
                    sec = "B"
                    marks = 5
                else:
                    sec = "C"
                    marks = 10
                
                sections[sec].append(cand)
                total_marks += marks
                
                # Prepare Item
                item = SamplePaperItem(
                    ordering=i+1, # Global ordering for now
                    candidate_id=cand.id,
                    marks=marks,
                    origin_type=cand.scores_json.get("origin", "unknown"),
                    notes=f"Section {sec}"
                )
                items_to_create.append(item)

            # 3. Create SamplePaper Record
            # Get next version number
            stmt_ver = select(func.max(SamplePaper.version))
            result_ver = await session.execute(stmt_ver)
            max_ver = result_ver.scalar() or 0
            new_ver = max_ver + 1
            
            paper = SamplePaper(
                version=new_ver,
                total_marks=total_marks,
                coverage_metrics_json={"candidate_count": len(candidates)}
            )
            session.add(paper)
            await session.flush()
            
            # Link items
            for item in items_to_create:
                item.paper_id = paper.id
                session.add(item)
            
            await session.commit()
            
            # 4. Generate Markdown
            md_lines = []
            md_lines.append(f"# {title}")
            md_lines.append(f"**Total Marks:** {total_marks} | **Time:** 3 Hours")
            md_lines.append("***")
            
            # Section A
            if sections["A"]:
                md_lines.append("\n## Section A (Short Answer) - 2 Marks Each")
                for idx, cand in enumerate(sections["A"], 1):
                    q = cand.normalized_question
                    md_lines.append(f"**Q{idx}.** {q.base_form}")
            
            # Section B
            if sections["B"]:
                md_lines.append("\n## Section B (Medium Answer) - 5 Marks Each")
                for idx, cand in enumerate(sections["B"], 1):
                    q = cand.normalized_question
                    md_lines.append(f"**Q{idx}.** {q.base_form}")
            
            # Section C
            if sections["C"]:
                md_lines.append("\n## Section C (Long Answer) - 10 Marks Each")
                for idx, cand in enumerate(sections["C"], 1):
                    q = cand.normalized_question
                    md_lines.append(f"**Q{idx}.** {q.base_form}")
            
            final_md = "\n".join(md_lines)
            logger.info(f"Sample Paper {paper.id} (v{new_ver}) generated successfully.")
            
            return final_md, paper.id

        except Exception as e:
            logger.error(f"Error generating sample paper: {e}")
            await session.rollback()
            raise
        break

if __name__ == "__main__":
    pass
