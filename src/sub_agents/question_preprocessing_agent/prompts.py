from langchain_core.prompts import ChatPromptTemplate

CONCEPT_STEM_PROMPT = ChatPromptTemplate.from_template(
    """
    You are an expert exam curator. Your task is to identify the **Single Core Concept** that unifies a group of similar questions and write a **Canonical Stem**.
    
    Input Questions:
    {questions}
    
    Instructions:
    1. Analyze the intent and core concept of all the input questions.
    2. Write a **Canonical Stem** that describes the *concept* being tested (e.g., "Calculate head movement using disk scheduling algorithms").
    3. This is **NOT** a final exam question. Do **NOT** create a multi-part question (e.g., "Calculate i, ii, iii").
    4. Keep it concise, neutral, and academic.
    5. If the questions ask for specific algorithms (FIFO, SSTF), generalize it to the topic (Disk Scheduling Algorithms) unless all questions ask for the exact same specific one.
    
    Canonical Concept Stem:
    """
)
