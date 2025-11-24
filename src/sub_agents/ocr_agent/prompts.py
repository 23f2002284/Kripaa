# 2. Construct Prompt for LLM
system_prompt = """You are an expert exam paper parser. Your task is to extract questions from the provided exam paper text.
Identify the Section, Question Number, Question Text, and Marks for each question.
Return the output strictly as a JSON array of objects.
"""

user_prompt = """
Extract ALL questions from the following exam paper content.
The content is in Markdown format.

### CRITICAL INSTRUCTIONS:
1.  **EXTRACT EVERY SINGLE QUESTION:** Do not skip any question. Do not summarize.
2.  **HANDLE SUB-QUESTIONS:** If a question has parts (e.g., 1(a), 1(b), or i, ii, iii), extract EACH part as a separate entry.
    *   Example: If Question 1 has parts (a) and (b), output TWO objects: one for "1(a)" and one for "1(b)".
3.  **SHORT QUESTIONS (Part-I):** Often, the first section contains many short questions (e.g., "Answer all 10 questions"). You MUST extract all 10 of them individually.
    *   Do NOT output a single item like "Answer all questions".
    *   If they are numbered i, ii, iii... or a, b, c..., use that as `original_numbering` (e.g., "1(i)", "1(ii)").
4.  **MARKS:**
    *   If marks are given per question (e.g., "[2]"), use that.
    *   If marks are given for a group (e.g., "Answer all. 2 x 10 = 20"), assign the individual mark (2) to EACH question.
5.  **TEXT:** Copy the question text EXACTLY as it appears.

For each question, extract:
- original_numbering: The question number (e.g., "1", "2(a)", "Q1", "1(i)").
- raw_text: The full text of the question. **PRESERVE MARKDOWN FORMATTING** (bold, italics, tables, code blocks, math notation, etc.).
- marks: The marks allocated to the question (as an integer).
- section: The section name (e.g., "Section A", "Part-I").
- year: The year of the examination (e.g., 2023). Infer from header.

Output Format:
[
    {{
        "original_numbering": "...",
        "raw_text": "...",
        "marks": ...,
        "section": "...",
        "year": ...
    }}
]

Exam Paper Content:
{md_text}
"""

syllabus_system_prompt = """You are an expert curriculum parser. Your task is to extract the syllabus structure from the provided document.
Identify Units, Chapters, and Topics, maintaining their hierarchy.
Return the output strictly as a JSON array of objects.
"""

syllabus_user_prompt = """
Extract the syllabus topics from the following content.
The content is in Markdown format.

For each topic/unit, extract:
- name: The title of the unit or topic.
- description: Brief summary. Do NOT list sub-topics here; extract them as separate child nodes with a deeper level.
- parent_name: The name of the parent unit/topic if it's a sub-topic. If it's a top-level unit, leave null.
- level: The hierarchy level (1 for Unit/Module, 2 for Chapter/Sub-unit, 3 for Topic/Sub-point).
- estimated_hours: Estimated teaching hours if mentioned.

Output Format:
[
    {{
        "name": "...",
        "description": "...",
        "parent_name": "...",
        "level": ...,
        "estimated_hours": ...
    }}
]

Syllabus Content:
{md_text}
"""
