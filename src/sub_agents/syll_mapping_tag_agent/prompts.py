from langchain_core.prompts import ChatPromptTemplate


# --- Prompts ---

TAGGING_PROMPT = ChatPromptTemplate.from_template(
    """
    You are an expert educational analyst. Your task is to analyze a batch of exam questions and assign metadata to each.
    
    For each question, determine:
    1. **Difficulty**: A scale of 1 to 5.
       - 1: Very Easy (Direct recall, simple definition)
       - 2: Easy (Basic understanding, simple explanation)
       - 3: Medium (Application of concepts, standard problems)
       - 4: Hard (Analysis, complex problems, multi-step reasoning)
       - 5: Very Hard (Evaluation, creation, novel scenarios, deep synthesis)
       
    2. **Taxonomy**: The cognitive level based on Bloom's Taxonomy. Choose one or more from:
       - Recall
       - Understand
       - Apply
       - Analyze
       - Evaluate
       - Create
    
    Input Questions:
    {questions_text}
    
    Output a JSON object with a list of tags, ensuring the 'question_id' matches the input exactly.
    """
)