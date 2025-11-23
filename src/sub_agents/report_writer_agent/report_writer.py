import asyncio
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from utils.db import get_session
from utils.logger import get_logger
from utils.pdf_generator import markdown_to_pdf
from utils.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate
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

NARRATIVE_PROMPT = ChatPromptTemplate.from_template("""
Generate a professional, insightful narrative for the "{section}" section of an academic report.

Context:
{context}

Requirements:
- Write in formal academic tone
- Highlight key patterns and insights
- Be specific with numbers and percentages
- Explain implications and significance
- Keep it concise (150-200 words)
""")

async def generate_narrative(section: str, context: str) -> str:
    llm = get_llm(temperature=0.3)
    chain = NARRATIVE_PROMPT | llm
    response = await chain.ainvoke({"section": section, "context": context})
    return response.content.strip()

async def generate_comprehensive_report(snapshot_id: UUID):
    logger.info("Generating Comprehensive Report...")
    md = []
    
    async for session in get_session():
        # === DATA COLLECTION ===
        
        # 1. Raw Questions
        stmt_raw = select(QuestionRaw)
        raw_questions = (await session.execute(stmt_raw)).scalars().all()
        
        # 2. Variant Groups
        stmt_vg = select(VariantGroup).options(selectinload(VariantGroup.syllabus_node))
        variant_groups = (await session.execute(stmt_vg)).scalars().all()
        
        # 3. Normalized Questions
        stmt_norm = select(QuestionNormalized)
        norm_questions = (await session.execute(stmt_norm)).scalars().all()
        
        # 4. Syllabus Nodes
        stmt_syll = select(SyllabusNode)
        syllabus_nodes = (await session.execute(stmt_syll)).scalars().all()
        
        # 5. Trend Snapshot
        stmt_snap = select(TrendSnapshot).where(TrendSnapshot.id == snapshot_id)
        snapshot = (await session.execute(stmt_snap)).scalar_one_or_none()
        
        # 6. Candidates
        stmt_cand = select(PredictionCandidate).options(
            selectinload(PredictionCandidate.normalized_question)
        ).where(PredictionCandidate.trend_snapshot_id == snapshot_id)
        candidates = (await session.execute(stmt_cand)).scalars().all()
        
        # 7. Sample Paper
        stmt_paper = select(SamplePaper).options(
            selectinload(SamplePaper.items)
        ).order_by(SamplePaper.generation_timestamp.desc()).limit(1)
        paper = (await session.execute(stmt_paper)).scalar_one_or_none()
        
        # === REPORT GENERATION ===
        
        md.append("# Comprehensive Exam Generation Report")
        md.append("**Kripaa AI - Automated Question Paper Generation System**\n")
        md.append("---\n")
        
        # === EXECUTIVE SUMMARY ===
        md.append("## Executive Summary\n")
        exec_context = f"""
        - Total Raw Questions: {len(raw_questions)}
        - Unique Concepts (Variant Groups): {len(variant_groups)}
        - Normalized Questions: {len(norm_questions)}
        - Syllabus Topics: {len(syllabus_nodes)}
        - Final Candidates: {len(candidates)}
        - Selected Questions: {len([c for c in candidates if c.status == CandidateStatus.selected])}
        """
        exec_narrative = await generate_narrative("Executive Summary", exec_context)
        md.append(exec_narrative + "\n")
        
        # === CHAPTER 1: DATA INGESTION ===
        md.append("## Chapter 1: Data Ingestion & Preprocessing\n")
        md.append("### 1.1 Raw Question Database\n")
        
        # Stats by year
        year_stats = {}
        for q in raw_questions:
            year_stats[q.year] = year_stats.get(q.year, 0) + 1
        
        md.append("| Year | Question Count | Percentage |")
        md.append("|------|----------------|------------|")
        total_raw = len(raw_questions)
        for year in sorted(year_stats.keys()):
            count = year_stats[year]
            pct = (count / total_raw) * 100 if total_raw else 0
            md.append(f"| {year} | {count} | {pct:.1f}% |")
        md.append("")
        
        ingest_context = f"Processed {len(raw_questions)} questions from {len(year_stats)} years. Average {total_raw / len(year_stats):.0f} questions per year."
        ingest_narrative = await generate_narrative("Data Ingestion Analysis", ingest_context)
        md.append(ingest_narrative + "\n")

        # Combined, readable raw question listing
        md.append("### 1.2 Raw Questions (Chronological, Grouped by Year)\n")
        for year in sorted(year_stats.keys()):
            md.append(f"#### Year: {year}\n")
            year_questions = [q for q in raw_questions if q.year == year]
            for rq in sorted(year_questions, key=lambda x: (x.marks or 0), reverse=True):
                md.append(f"- **Marks:** {rq.marks or '-'} | **Source:** {rq.source_pdf or '-'}\n  ")
                md.append(f"  {rq.raw_text.replace('|', ' ')}\n")
        md.append("")
        
        # === CHAPTER 2: VARIANT GROUPING ===
        md.append("## Chapter 2: Variant Detection & Grouping\n")
        md.append("### 2.1 Concept Clustering\n")
        
        md.append(f"**Total Variant Groups:** {len(variant_groups)}\n")
        md.append(f"**Compression Ratio:** {total_raw / len(variant_groups):.2f}:1\n")
        
        recurrence_dist = {}
        for vg in variant_groups:
            rec = vg.recurrence_count
            recurrence_dist[rec] = recurrence_dist.get(rec, 0) + 1
        
        md.append("#### Recurrence Distribution\n")
        md.append("| Recurrence | Groups | Description |")
        md.append("|------------|--------|-------------|")
        for rec in sorted(recurrence_dist.keys(), reverse=True):
            count = recurrence_dist[rec]
            desc = "Highly repeated" if rec >= 5 else "Moderately repeated" if rec >= 3 else "Rarely repeated"
            md.append(f"| {rec} times | {count} | {desc} |")
        md.append("")
        
        variant_context = f"Created {len(variant_groups)} concept groups from {total_raw} raw questions, achieving {total_raw / len(variant_groups):.1f}x compression."
        variant_narrative = await generate_narrative("Variant Grouping Insights", variant_context)
        md.append(variant_narrative + "\n")

        # Variant groups as readable blocks, sorted by recurrence
        md.append("### 2.2 Variant Groups (Sorted by Recurrence)\n")
        for vg in sorted(variant_groups, key=lambda x: x.recurrence_count, reverse=True):
            mapped_topic = vg.syllabus_node.topic if vg.syllabus_node_id and vg.syllabus_node else "-"
            md.append(f"- **Recurrence:** {vg.recurrence_count} | **First Year:** {vg.first_year or '-'} | **Last Year:** {vg.last_year or '-'} | **Topic:** {mapped_topic}\n  ")
            md.append(f"  {vg.canonical_stem.replace('|', ' ')}\n")
        md.append("")
        
        # === CHAPTER 3: SYLLABUS MAPPING ===
        md.append("## Chapter 3: Syllabus Alignment\n")
        md.append("### 3.1 Topic Coverage\n")
        
        mapped_vgs = [vg for vg in variant_groups if vg.syllabus_node_id]
        coverage_pct = (len(mapped_vgs) / len(variant_groups)) * 100 if variant_groups else 0
        
        md.append(f"**Mapped Variant Groups:** {len(mapped_vgs)} / {len(variant_groups)} ({coverage_pct:.1f}%)\n")
        
        # Module breakdown
        module_stats = {}
        for node in syllabus_nodes:
            module_stats[node.module] = module_stats.get(node.module, 0) + 1
        
        md.append("#### Syllabus Module Distribution\n")
        md.append("| Module | Topics | Percentage |")
        md.append("|--------|--------|------------|")
        total_topics = len(syllabus_nodes)
        for module in sorted(module_stats.keys()):
            count = module_stats[module]
            pct = (count / total_topics) * 100 if total_topics else 0
            md.append(f"| {module} | {count} | {pct:.1f}% |")
        md.append("")
        
        syll_context = f"{coverage_pct:.1f}% of questions mapped to {len(syllabus_nodes)} syllabus topics across {len(module_stats)} modules."
        syll_narrative = await generate_narrative("Syllabus Mapping Analysis", syll_context)
        md.append(syll_narrative + "\n")

        # Detailed syllabus node listing
        md.append("### 3.2 Syllabus Node Listing\n")
        md.append("| ID | Module | Topic | Level | Times Asked | Gap Score | Status |")
        md.append("|----|--------|-------|------:|-----------:|---------:|--------|")
        for node in syllabus_nodes:
            md.append(f"| {str(node.id)[:8]} | {node.module} | {node.topic} | {node.level} | {node.times_asked} | {node.gap_score:.2f} | {node.status.value} |")
        md.append("")
        
        # === CHAPTER 4: TREND ANALYSIS ===
        md.append("## Chapter 4: Trend Analysis\n")
        
        if snapshot:
            md.append("### 4.1 Historical Patterns\n")
            
            topic_stats = snapshot.topic_stats_json or {}
            if "_meta" in topic_stats:
                meta = topic_stats["_meta"]
                md.append(f"**LLM Insight:** {meta.get('qualitative_insight', 'N/A')}\n")
            
            # Emerging topics
            emerging_count = len(snapshot.emerging_topics or [])
            declining_count = len(snapshot.declining_topics or [])
            
            md.append(f"**Emerging Topics:** {emerging_count}\n")
            md.append(f"**Declining Topics:** {declining_count}\n")
            
            trend_context = f"Identified {emerging_count} emerging and {declining_count} declining topics through multi-year analysis."
            trend_narrative = await generate_narrative("Trend Analysis Summary", trend_context)
            md.append(trend_narrative + "\n")

            # Emerging & declining topic details if resolvable
            md.append("### 4.2 Emerging / Declining Topics Details\n")
            md.append("| Topic ID | Type |")
            md.append("|----------|------|")
            for t in (snapshot.emerging_topics or []):
                md.append(f"| {str(t)[:8]} | emerging |")
            for t in (snapshot.declining_topics or []):
                md.append(f"| {str(t)[:8]} | declining |")
            md.append("")
        
        # === CHAPTER 5: QUESTION GENERATION ===
        md.append("## Chapter 5: Question Generation Strategy\n")
        md.append("### 5.1 Candidate Pool Creation\n")
        
        origin_dist = {}
        for c in candidates:
            origin = c.scores_json.get("origin", "unknown")
            origin_dist[origin] = origin_dist.get(origin, 0) + 1
        
        md.append("| Origin Type | Count | Strategy |")
        md.append("|-------------|-------|----------|")
        for origin in sorted(origin_dist.keys()):
            count = origin_dist[origin]
            strategy = "Reused from history" if origin == "historical" else "LLM-generated variation" if "variant" in origin else "Novel LLM creation"
            md.append(f"| {origin} | {count} | {strategy} |")
        md.append("")
        
        gen_context = f"Generated {len(candidates)} candidates: {origin_dist.get('historical', 0)} historical, {origin_dist.get('generated_variant', 0)} variants, {origin_dist.get('generated_novel', 0)} novel."
        gen_narrative = await generate_narrative("Generation Strategy Analysis", gen_context)
        md.append(gen_narrative + "\n")

        # Candidate listing as readable blocks, sorted by status and marks
        md.append("### 5.2 Candidate Questions (Sorted by Status, Marks)\n")
        for c in sorted(candidates, key=lambda x: (x.status.value, -(x.normalized_question.marks or 0) if x.normalized_question else 0)):
            nq = c.normalized_question
            origin = c.scores_json.get("origin", "-")
            md.append(f"- **Status:** {c.status.value} | **Origin:** {origin} | **Difficulty:** {nq.difficulty if nq and nq.difficulty is not None else '-'} | **Marks:** {nq.marks if nq and nq.marks is not None else '-'}\n  ")
            md.append(f"  {nq.base_form.replace('|', ' ') if nq else '-'}\n")
        md.append("")
        
        # === CHAPTER 6: VOTING & SELECTION ===
        md.append("## Chapter 6: Voting & Selection Process\n")
        md.append("### 6.1 Quality Control\n")
        
        selected = [c for c in candidates if c.status == CandidateStatus.selected]
        excluded = [c for c in candidates if c.status == CandidateStatus.excluded]
        
        md.append(f"**Selected:** {len(selected)}\n")
        md.append(f"**Excluded:** {len(excluded)}\n")
        md.append(f"**Selection Rate:** {(len(selected) / len(candidates)) * 100:.1f}%\n")
        
        # Exclusion reasons
        exclusion_reasons = {}
        for c in excluded:
            reason = c.scores_json.get("exclusion_reason", "Unknown")
            if "(" in reason:
                reason = reason.split("(")[0].strip()
            exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
        
        if exclusion_reasons:
            md.append("#### Exclusion Breakdown\n")
            md.append("| Reason | Count | Impact |")
            md.append("|--------|-------|--------|")
            for reason, count in sorted(exclusion_reasons.items(), key=lambda x: x[1], reverse=True):
                impact = f"{(count / len(excluded)) * 100:.1f}% of exclusions" if excluded else "0%"
                md.append(f"| {reason} | {count} | {impact} |")
            md.append("")
        
        vote_context = f"Selected {len(selected)} from {len(candidates)} candidates through relevance and diversity filtering."
        vote_narrative = await generate_narrative("Selection Process Analysis", vote_context)
        md.append(vote_narrative + "\n")
        
        # === CHAPTER 7: FINAL PAPER ===
        md.append("## Chapter 7: Final Sample Paper\n")
        
        if paper:
            md.append(f"**Paper ID:** `{paper.id}`\n")
            md.append(f"**Total Marks:** {paper.total_marks}\n")
            md.append(f"**Questions:** {len(paper.items or [])}\n")
            
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
            
            md.append("\n#### Paper Structure\n")
            md.append("| Section | Questions | Marks Each | Total Marks |")
            md.append("|---------|-----------|------------|-------------|")
            md.append(f"| A (Short) | {section_stats['A']} | 2 | {section_stats['A'] * 2} |")
            md.append(f"| B (Medium) | {section_stats['B']} | 5 | {section_stats['B'] * 5} |")
            md.append(f"| C (Long) | {section_stats['C']} | 10 | {section_stats['C'] * 10} |")
            md.append("")
            
            paper_context = f"Assembled {len(paper.items or [])} questions totaling {paper.total_marks} marks."
            paper_narrative = await generate_narrative("Final Paper Assembly", paper_context)
            md.append(paper_narrative + "\n")

            # Detailed paper item listing
            md.append("### 7.1 Paper Item Listing\n")
            md.append("| Ord | Marks | Origin | Notes | Candidate ID |")
            md.append("|----:|------:|--------|-------|--------------|")
            for it in (paper.items or []):
                md.append(f"| {it.ordering} | {it.marks or ''} | {it.origin_type or ''} | {(it.notes or '')[:40]} | {str(it.candidate_id)[:8] if it.candidate_id else ''} |")
            md.append("")

        # Normalized questions as readable blocks, sorted by marks
        md.append("## Appendix A: Normalized Questions (Sorted by Marks)\n")
        for nq in sorted(norm_questions, key=lambda x: -(x.marks or 0)):
            md.append(f"- **Marks:** {nq.marks if nq.marks is not None else '-'} | **Difficulty:** {nq.difficulty if nq.difficulty is not None else '-'} | **Variant Group:** {str(nq.variant_group_id)[:8] if nq.variant_group_id else '-'}\n  ")
            md.append(f"  {nq.base_form.replace('|', ' ')}\n")
        md.append("")

        md.append("## Appendix B: Data Model Summary\n")
        md.append("The following appendices enumerate the core entities captured during the pipeline, supporting transparency and reproducibility for academic judging.")
        
        # === CONCLUSION ===
        md.append("## Conclusion\n")
        conclusion = await generate_narrative(
            "Project Conclusion",
            f"Successfully generated exam paper from {len(raw_questions)} historical questions using AI-driven trend analysis and ensemble generation."
        )
        md.append(conclusion + "\n")
        
        final_md = "\n".join(md)
        
        # Generate PDF
        markdown_to_pdf(final_md, "comprehensive_report.pdf", title="Kripaa Comprehensive Report")
        logger.info("Comprehensive Report Generated: comprehensive_report.pdf")
        
        break

if __name__ == "__main__":
    pass
