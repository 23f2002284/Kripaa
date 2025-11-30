from langchain_core.prompts import ChatPromptTemplate

# Section A: Short Answer (2 Marks) - Difficulty 1-2
SHORT_ANSWER_VARIANT_PROMPT = ChatPromptTemplate.from_template("""
You are creating a SHORT ANSWER exam question (2 marks) by rewriting the following question.

ORIGINAL QUESTION:
{original_question}

REQUIREMENTS:
- Keep it SHORT (1-3 sentences maximum)
- Difficulty: EASY (Level 1-2)
- Bloom's Taxonomy: Remember or Understand
- Focus: Definitions, basic concepts, simple explanations
- Maintain the core concept but vary the wording
- Do NOT add complexity or numerical problems

OUTPUT: Just the rewritten question text (no explanations).
""")

SHORT_ANSWER_NOVEL_PROMPT = ChatPromptTemplate.from_template("""
You are creating a NEW SHORT ANSWER exam question (2 marks).

TOPIC: {topic_name}
MODULE: {module_name}

REQUIREMENTS:
- Length: 1-3 sentences maximum
- Difficulty: EASY (Level 1-2)
- Bloom's Taxonomy: Remember or Understand
- Question Types: "Define...", "What is...", "List...", "State...", "Explain briefly..."
- Focus: Core concepts, terminology, basic principles
- Do NOT create problem-solving or analysis questions

OUTPUT: Just the question text (no explanations).
""")

# Section B: Medium Answer (5 Marks) - Difficulty 3
MEDIUM_ANSWER_VARIANT_PROMPT = ChatPromptTemplate.from_template("""
You are creating a MEDIUM ANSWER exam question (5 marks) by rewriting the following question.

ORIGINAL QUESTION:
{original_question}

REQUIREMENTS:
- Length: Appropriate length question just like questions in pyqs
- Difficulty: MEDIUM (Level 3)
- Bloom's Taxonomy: Apply or Analyze
- Focus: Procedures, comparisons, applications, algorithms
- Structure: Can be a single detailed question or split into parts (e.g., a) and b))
- Style: Academic but direct, typical of engineering semester exams
- Maintain the core concept but vary the scenario or parameters
- Can include simple numerical values if appropriate

OUTPUT: Just the rewritten question text (no explanations).
""")

MEDIUM_ANSWER_NOVEL_PROMPT = ChatPromptTemplate.from_template("""
You are creating a NEW MEDIUM ANSWER exam question (5 marks).

TOPIC: {topic_name}
MODULE: {module_name}

REQUIREMENTS:
- Length: Appropriate length question just like questions in pyqs
- Difficulty: MEDIUM (Level 3)
- Bloom's Taxonomy: Apply or Analyze
- Question Types: "Explain...", "Describe the process...", "Compare and contrast...", "Solve...", "Analyze..."
- Focus: Application of concepts, procedures, analysis
- Structure: Can be split into sub-parts
- Avoid: Overly complex case studies unless typical for the topic. Keep it solvable within exam time limits.

OUTPUT: Just the question text (no explanations).
""")

# Section C: Long Answer (10 Marks) - Difficulty 4-5
LONG_ANSWER_VARIANT_PROMPT = ChatPromptTemplate.from_template("""
You are creating a LONG ANSWER exam question (10 marks) by rewriting the following question.

ORIGINAL QUESTION:
{original_question}

REQUIREMENTS:
- Length: Standard long answer (approx. 300-400 words expected answer)
- Difficulty: Moderate to Hard (Level 3-4)
- Bloom's Taxonomy: Analyze, Evaluate, or Apply
- Focus: Clear explanation, discussion, or comparison of concepts
- Structure: Can be a single detailed question or split into parts (e.g., a) and b))
- Style: Academic but direct, typical of engineering semester exams
- Maintain the core concept but vary the approach or scenario

OUTPUT: Just the rewritten question text (no explanations).
""")

LONG_ANSWER_NOVEL_PROMPT = ChatPromptTemplate.from_template("""
You are creating a NEW LONG ANSWER exam question (10 marks).

TOPIC: {topic_name}
MODULE: {module_name}

REQUIREMENTS:
- Length: Standard long answer (10 marks)
- Difficulty: Moderate to Hard
- Bloom's Taxonomy: Analyze, Explain, Discuss
- Question Types: "Explain in detail...", "Discuss the significance of...", "Compare and contrast...", "Describe the process of..."
- Focus: Conceptual clarity and detailed understanding
- Structure: Can be split into sub-parts (e.g., Define X and explain Y)
- Avoid: Overly complex case studies unless typical for the topic. Keep it solvable within exam time limits.

OUTPUT: Just the question text (no explanations).
""")

# Legacy prompts (kept for backward compatibility if needed)
VARIANT_GENERATION_PROMPT = SHORT_ANSWER_VARIANT_PROMPT
NOVEL_GENERATION_PROMPT = SHORT_ANSWER_NOVEL_PROMPT
