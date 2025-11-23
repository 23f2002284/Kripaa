from langchain_core.prompts import ChatPromptTemplate

TREND_ANALYSIS_PROMPT = ChatPromptTemplate.from_template(
    """
    You are an expert educational data analyst. You have analyzed the historical trends of exam questions for a Computer Science course.
    
    Here is a summary of the key trends found:
    
    **Emerging Topics (Rising Frequency):**
    {emerging_topics}
    
    **Declining Topics (Falling Frequency):**
    {declining_topics}
    
    **High Gap Topics (Due for recurrence):**
    {gap_topics}
    
    **Taxonomy Shifts (Cognitive Level Changes):**
    {taxonomy_shifts}
    
    **Instructions:**
    1. Write a concise, executive summary (max 200 words) explaining the most significant shifts in the exam pattern.
    2. Highlight if the exam is becoming more practical/analytical or staying theoretical.
    3. Mention specific modules or topics that are becoming critical.
    4. Provide a strategic recommendation for students preparing for the next exam.
    
    **Trend Insight:**
    """
)
