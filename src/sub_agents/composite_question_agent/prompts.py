from langchain_core.prompts import ChatPromptTemplate

COMPOSITE_MASTER_PROMPT = ChatPromptTemplate.from_template(
    """
    You are an expert exam curator. Your task is to create a **Master Composite Question** (Exam-Level) based on a group of similar questions.
    
    **Concept Stem**: {canonical_stem}
    
    **Variant Questions**:
    {variants}
    
    **Instructions**:
    1. Create a single, high-quality exam question that comprehensively tests this concept.
    2. **Multi-Part Questions**: If the variants ask for different specific things (e.g., one asks for FIFO, another for SSTF), combine them into a multi-part question (e.g., "Calculate using: (i) FIFO, (ii) SSTF").
    3. **Completeness**: Ensure the question covers the scope of all provided variants.
    4. **Clarity**: The question should be clear, unambiguous, and written in standard academic English.
    5. **Format**: 
       - If it's a simple concept, just write the question.
       - If it needs parts, use (a), (b) or (i), (ii).
    6. **Do NOT** answer the question. Just write the question itself.
    
    **Master Composite Question**:
    """
)
