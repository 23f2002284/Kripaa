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
Extract ALL topics, units, modules, and chapters from the following syllabus PDF document.

### CRITICAL INSTRUCTIONS:
1.  **EXTRACT EVERY SINGLE ITEM:** Do not skip any unit, module, chapter, section, sub-topic, or concept. Do not summarize or merge items.

2.  **IDENTIFY HIERARCHY FROM FORMATTING:**
    - **Level 1 (Modules/Units):** Usually titled "MODULE I", "UNIT 1", "PART A" - often in bold/large font or numbered with Roman numerals (I, II, III) or numbers (1, 2, 3).
    - **Level 2 (Main Topics/Sections):** The primary topics under a module - often bold or slightly indented. These are the main subject areas.
    - **Level 3 (Sub-topics/Concepts):** Specific concepts, points, or details under a main topic - often bulleted, indented further, or in plain text.
    
3.  **HIERARCHY EXAMPLES:**
    - "MODULE I" → Level 1 (parent_name: null)
    - "Industrial Safety" (under MODULE I) → Level 2 (parent_name: "MODULE I")
    - "Accidents" (under Industrial Safety) → Level 3 (parent_name: "Industrial Safety")
    - "Causes" (under Industrial Safety) → Level 3 (parent_name: "Industrial Safety")
    - "Types" (under Industrial Safety) → Level 3 (parent_name: "Industrial Safety")

4.  **SPLIT COMPOUND TOPICS:** If you see "Mechanical/Electrical Hazards", create SEPARATE entries:
    - "Mechanical Hazards" (Level 3, parent: relevant Level 2 topic)
    - "Electrical Hazards" (Level 3, parent: relevant Level 2 topic)
    
5.  **SPLIT LISTS:** If you see "Accidents, causes, types, results and control", create SEPARATE entries for each:
    - "Accidents"
    - "Causes"  
    - "Types"
    - "Results"
    - "Control measures"
    Each should have the SAME parent (the main topic they belong to).

6.  **VISUAL CUES FOR HIERARCHY:**
    - **Bold/Larger text** = Usually Level 1 or Level 2
    - **Indentation/Bullets** = Usually Level 3
    - **Numbering** = Roman numerals (I, II) = Level 1; Letters (a, b) or numbers (1, 2) = Level 2 or 3
    - **Context** = If a topic introduces subtopics, it's a parent (Level 1 or 2). The subtopics are children (Level 2 or 3).

For each topic/unit/module/chapter, extract:
- name: The exact title/name. Keep it concise - single concept per entry (e.g., "Accidents", not "Accidents, causes, types").
- description: Brief summary if available. If not, use null.
- parent_name: The name of the parent. Match the exact name you used for the parent entry.
- level: Hierarchy level (1=Module, 2=Main Topic, 3=Sub-topic/Concept).
- estimated_hours: Teaching hours if mentioned, otherwise null.

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
