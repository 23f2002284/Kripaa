import asyncio
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from utils.db import get_session
from utils.logger import get_logger
from utils.simple_pdf_generator import generate_simple_exam_pdf
from src.data_models.models import (
    QuestionRaw,
    VariantGroup,
    QuestionNormalized,
    SyllabusNode,
    TrendSnapshot,
    PredictionCandidate,
    SamplePaper,
    SamplePaperItem,
    CandidateStatus
)

logger = get_logger()

async def generate_comprehensive_report(snapshot_id: UUID, output_dir: str = "."):
    """Generate a comprehensive, data-driven report without LLM calls."""
    logger.info("Generating Comprehensive Report...")
    md = []
    
    # Convert output_dir to Path
    from pathlib import Path
    output_path = Path(output_dir)
    
    async for session in get_session():
        # === DATA COLLECTION ===
        
        # Fetch all data
        stmt_raw = select(QuestionRaw)
        raw_questions = (await session.execute(stmt_raw)).scalars().all()
        
        stmt_vg = select(VariantGroup).options(selectinload(VariantGroup.syllabus_node))
        variant_groups = (await session.execute(stmt_vg)).scalars().all()
        
        stmt_snap = select(TrendSnapshot).where(TrendSnapshot.id == snapshot_id)
        snapshot = (await session.execute(stmt_snap)).scalar_one_or_none()
        
        stmt_cand = select(PredictionCandidate).options(
            selectinload(PredictionCandidate.normalized_question)
        ).where(PredictionCandidate.trend_snapshot_id == snapshot_id)
        candidates = (await session.execute(stmt_cand)).scalars().all()
        
        stmt_paper = select(SamplePaper).options(
            selectinload(SamplePaper.items)
        ).order_by(SamplePaper.generation_timestamp.desc()).limit(1)
        paper = (await session.execute(stmt_paper)).scalar_one_or_none()
        
        # === REPORT CONSTRUCTION ===
        
        md.append("# Kripaa - Comprehensive Exam Generation Report")
        md.append("")
        md.append(f"**Snapshot ID:** {snapshot_id}")
        md.append(f"**Generated:** {snapshot.created_at.strftime('%Y-%m-%d %H:%M') if snapshot else 'N/A'}")
        md.append("")
        md.append("---")
        md.append("")
        
        # === EXECUTIVE SUMMARY ===
        md.append("## Executive Summary")
        md.append("")
        md.append(f"- **Total Raw Questions Processed:** {len(raw_questions)}")
        md.append(f"- **Unique Concept Groups (Variants):** {len(variant_groups)}")
        md.append(f"- **Compression Ratio:** {len(raw_questions) / len(variant_groups):.2f}:1")
        md.append(f"- **Total Candidates Generated:** {len(candidates)}")
        md.append(f"- **Final Questions Selected:** {len([c for c in candidates if c.status == CandidateStatus.selected])}")
        md.append(f"- **Final Paper Marks:** {paper.total_marks if paper else 0}")
        md.append("")
        
        # === TREND ANALYSIS OUTPUT ===
        md.append("## Trend Analysis Results")
        md.append("")
        
        if snapshot:
            md.append(f"**Year Range:** {snapshot.year_range[0]}-{snapshot.year_range[1]}")
            md.append(f"**Emerging Topics:** {len(snapshot.emerging_topics or [])}")
            md.append(f"**Declining Topics:** {len(snapshot.declining_topics or [])}")
            md.append("")
            
            topic_stats = snapshot.topic_stats_json or {}
            
            # Show sample topics with enhancements
            md.append("### Topic Analysis (Enhanced with Section-Awareness & Cyclicity)")
            md.append("")
            
            non_meta_topics = [(tid, data) for tid, data in topic_stats.items() if tid != "_meta"]
            
            for topic_id, data in non_meta_topics[:10]:  # Top 10 topics
                md.append(f"#### {data.get('name', 'Unknown Topic')}")
                md.append("")
                md.append(f"- **Module:** {data.get('module', 'Unknown')}")
                md.append(f"- **Status:** {data.get('status', 'stable')}")
                md.append(f"- **Gap Score:** {data.get('gap_score', 0)}")
                md.append(f"- **Last Asked:** {data.get('last_asked_year', 'N/A')}")
                md.append("")
                
                # Section Distribution
                section_dist = data.get('section_distribution', {})
                if section_dist:
                    a_pct = int(section_dist.get('A', 0) * 100)
                    b_pct = int(section_dist.get('B', 0) * 100)
                    c_pct = int(section_dist.get('C', 0) * 100)
                    md.append(f"- **Section Distribution:** A={a_pct}%, B={b_pct}%, C={c_pct}%")
                    md.append(f"- **Section Preference:** {data.get('section_preference', 'Unknown')}")
                    md.append(f"- **Average Difficulty:** {data.get('avg_difficulty', 0)}")
                    md.append("")
                
                # Cyclicity
                cyclicity = data.get('cyclicity', {})
                pattern = cyclicity.get('pattern_type', 'unknown')
                confidence = cyclicity.get('confidence', 0)
                
                md.append(f"- **Cyclicity Pattern:** {pattern}")
                
                if pattern == 'regular':
                    cycle = cyclicity.get('cycle_length')
                    next_year = cyclicity.get('next_expected_year')
                    md.append(f"  - Appears every {cycle} years")
                    md.append(f"  - Next expected: {next_year}")
                elif pattern in ['odd_years', 'even_years']:
                    next_year = cyclicity.get('next_expected_year')
                    md.append(f"  - Next expected: {next_year}")
                elif pattern == 'mostly_regular':
                    cycle = cyclicity.get('cycle_length')
                    md.append(f"  - Usually every {cycle} years")
                
                md.append(f"  - Confidence: {int(confidence * 100)}%")
                md.append("")
            
            # LLM Insight from Trend Analysis
            meta = topic_stats.get('_meta', {})
            insight = meta.get('qualitative_insight', '')
            if insight:
                md.append("### LLM Qualitative Insight (from Trend Analysis)")
                md.append("")
                md.append(insight)
                md.append("")
        
        # === QUESTION GENERATION ===
        md.append("## Question Generation Strategy")
        md.append("")
        
        origin_dist = {}
        section_dist = {"A": 0, "B": 0, "C": 0}
        temp_dist = {}
        
        for c in candidates:
            origin = c.scores_json.get("origin", "unknown")
            section = c.scores_json.get("section_target", "Unknown")
            temp = c.scores_json.get("llm_temperature", "N/A")
            
            origin_dist[origin] = origin_dist.get(origin, 0) + 1
            if section in section_dist:
                section_dist[section] += 1
            temp_dist[temp] = temp_dist.get(temp, 0) + 1
        
        md.append("### Candidate Pool Breakdown")
        md.append("")
        md.append("| Origin Type | Count | Description |")
        md.append("|-------------|-------|-------------|")
        md.append(f"| Historical | {origin_dist.get('historical', 0)} | Reused from past papers |")
        md.append(f"| Generated Variant | {origin_dist.get('generated_variant', 0)} | LLM-rewritten variations |")
        md.append(f"| Generated Novel | {origin_dist.get('generated_novel', 0)} | New LLM-created questions |")
        md.append("")
        
        md.append("### Section Distribution")
        md.append("")
        md.append("| Section | Candidates | Target Selection |")
        md.append("|---------|------------|------------------|")
        md.append(f"| A (Short) | {section_dist['A']} | 10 questions |")
        md.append(f"| B (Medium) | {section_dist['B']} | 12 questions |")
        md.append(f"| C (Long) | {section_dist['C']} | 5 questions |")
        md.append("")
        
        md.append("### Temperature Distribution (Multi-Temperature Ensemble)")
        md.append("")
        md.append("| Temperature | Count | Purpose |")
        md.append("|-------------|-------|---------|")
        for temp in sorted([t for t in temp_dist.keys() if t != "N/A"]):
            count = temp_dist[temp]
            purpose = "Conservative" if temp == 0.2 else "Balanced" if temp == 0.5 else "Creative"
            md.append(f"| {temp} | {count} | {purpose} |")
        md.append("")
        
        # === VOTING & SELECTION ===
        md.append("## Voting & Selection Results")
        md.append("")
        
        selected = [c for c in candidates if c.status == CandidateStatus.selected]
        excluded = [c for c in candidates if c.status == CandidateStatus.excluded]
        
        md.append(f"**Selected:** {len(selected)} / {len(candidates)}")
        md.append(f"**Excluded:** {len(excluded)}")
        if len(candidates) > 0:
            md.append(f"**Selection Rate:** {(len(selected) / len(candidates)) * 100:.1f}%")
        else:
            md.append(f"**Selection Rate:** N/A (no candidates generated)")
        md.append("")
        
        # Exclusion reasons
        exclusion_reasons = {}
        for c in excluded:
            reason = c.scores_json.get("exclusion_reason", "Unknown")
            category = c.scores_json.get("exclusion_category", "Other")
            exclusion_reasons[category] = exclusion_reasons.get(category, 0) + 1
        
        if exclusion_reasons:
            md.append("### Exclusion Breakdown")
            md.append("")
            md.append("| Category | Count | Percentage |")
            md.append("|----------|-------|------------|")
            for category, count in sorted(exclusion_reasons.items(), key=lambda x: x[1], reverse=True):
                pct = (count / len(excluded)) * 100 if excluded else 0
                md.append(f"| {category} | {count} | {pct:.1f}% |")
            md.append("")
        
        # === FINAL PAPER ===
        md.append("## Final Sample Paper")
        md.append("")
        
        if paper:
            md.append(f"**Paper ID:** {paper.id}")
            md.append(f"**Total Marks:** {paper.total_marks}")
            md.append(f"**Total Questions:** {len(paper.items or [])}")
            md.append("")
            
            # Section breakdown
            section_stats = {"A": 0, "B": 0, "C": 0}
            for item in (paper.items or []):
                notes = item.notes or ""
                if "Section A" in notes:
                    section_stats["A"] += 1
                elif "Section B" in notes:
                    section_stats["B"] += 1
                elif "Section C" in notes:
                    section_stats["C"] += 1
            
            md.append("### Paper Structure")
            md.append("")
            md.append("| Section | Questions | Marks Each | Total Marks |")
            md.append("|---------|-----------|------------|-------------|")
            md.append(f"| A (Short) | {section_stats['A']} | 2 | {section_stats['A'] * 2} |")
            md.append(f"| B (Medium) | {section_stats['B']} | 5 | {section_stats['B'] * 5} |")
            md.append(f"| C (Long) | {section_stats['C']} | 10 | {section_stats['C'] * 10} |")
            md.append(f"| **Total** | **{sum(section_stats.values())}** | - | **{paper.total_marks}** |")
            md.append("")
        
        # === CONCLUSION ===
        md.append("## Summary")
        md.append("")
        md.append("This report documents the complete pipeline from {len(raw_questions)} historical questions to a {paper.total_marks if paper else 0}-mark predicted exam paper using:")
        md.append("")
        md.append("1. **Enhanced Trend Analysis** with section-awareness and cyclicity detection")
        md.append("2. **Multi-Temperature Ensemble Generation** using gemini-2.5-pro (temps: 0.2, 0.5, 0.9)")
        md.append("3. **Section-Aware Voting** with detailed exclusion tracking")
        md.append("4. **Quality-Controlled Selection** ensuring diversity and relevance")
        md.append("")
        md.append("All data is stored in PostgreSQL for transparency and reproducibility.")
        md.append("")
        
        final_md = "\n".join(md)
        
        # Save markdown file
        md_file = output_path / "comprehensive_report.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(final_md)
        
        # Generate simple PDF
        pdf_file = output_path / "comprehensive_report.pdf"
        generate_simple_exam_pdf(str(md_file), str(pdf_file))
        logger.info(f"Comprehensive Report Generated: {pdf_file}")
        
        break

if __name__ == "__main__":
    pass
