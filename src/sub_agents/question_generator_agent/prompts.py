from langchain_core.prompts import ChatPromptTemplate

# Strategy 2: Variant Generation
# Takes an existing question and modifies it.
VARIANT_GENERATION_PROMPT = ChatPromptTemplate.from_template(
    """
    You are an expert exam question setter for a university Computer Science course. 
    Your task is to create a **variant** of an existing question that is strictly aligned with the syllabus.
    
    **Original Question:**
    {original_question}
    
    **Instructions:**
    1. **Strict Adherence**: The new question MUST test the exact same core concept as the original.
    2. **Style Match**: Maintain the same formal, academic tone and difficulty level. Do not make it conversational or overly scenario-based unless the original is.
    3. **Modification**: Change specific values, variable names, or the context slightly.
    4. **No Drift**: Do NOT introduce concepts outside the scope of the original question.
    5. Output ONLY the new question text.
    
    **New Question:**
    """
)

# Strategy 3: Novel Generation
# Creates a new question from scratch based on a topic.
NOVEL_GENERATION_PROMPT = ChatPromptTemplate.from_template(
    """
    You are an expert exam question setter for a university Computer Science course.
    Your task is to create a **brand new** question for a specific topic, strictly based on the syllabus.
    
    **Topic:** {topic_name}
    **Module:** {module_name}
    **Target Difficulty:** {difficulty} (1-5)
    **Cognitive Level:** {taxonomy}
    
    **Instructions:**
    1. **Syllabus Focused**: The question must be directly answerable using standard textbooks for this module. Do NOT ask niche or out-of-scope trivia.
    2. **Exam Pattern**: The question should sound exactly like it belongs in a formal written exam (concise, clear, unambiguous).
    3. **Cognitive Match**: Ensure the question matches the target cognitive level (e.g., 'Apply' should involve a small problem, 'Recall' should be a definition).
    4. **Avoid Randomness**: Do not create overly complex or bizarre scenarios. Stick to standard academic examples.
    5. Output ONLY the question text.
    
    **New Question:**
    """
)
