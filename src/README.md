# System Architecture & Agent Design

## 1. OCR Agent

### **Purpose**
The OCR Agent acts as the primary ingestion gateway. It is responsible for converting raw PDF documents (Previous Year Questions (PYQs) and Syllabus files) into structured data within our database.

### **Workflow**
1.  **Input:** Receives a single PDF file path (either a PYQ paper or a Syllabus document).
2.  **Extraction:** Uses `pymupdf4llm` to extract text while preserving layout (tables, headers) in Markdown format.
3.  **Parsing (LLM):** 
    *   **For PYQs:** The LLM parses the markdown to identify individual questions, marks, and sections, populating the `QuestionRaw` table.
    *   **For Syllabus:** The LLM parses the hierarchical structure (Unit -> Chapter -> Topic) and populates the `SyllabusNode` table.
4.  **Orchestration:** The agent is designed to be called sequentially in a loop by a higher-level orchestrator until all input PDFs are processed.

### **Design Decisions & Q&A**

> **Q1: Should we process all PDFs in a single massive context or orchestrate individual calls?**
> **Decision:** **Orchestrational/Sequential Calls.**
> *   **Reasoning:** Processing one PDF at a time is more robust. It isolates failures (if one PDF fails, others succeed), keeps the LLM context window focused and less prone to "lost-in-the-middle" hallucinations, and makes debugging easier.
> *   **Scale:** With ~5 PYQ papers (approx. 2 pages each) and 1 Syllabus (1-2 pages), the overhead of multiple API calls is negligible compared to the accuracy gains.

> **Q2: Should the LLM extraction be a single call per PDF or chunked?**
> **Decision:** **Single Call per PDF.**
> *   **Reasoning:** A single PYQ paper (approx. 26 questions) fits easily within modern LLM context windows (e.g., GPT-4o, Gemini 1.5).
> *   **Flow:** 
>     *   **Call 1-5 (PYQs):** Each call ingests one paper and creates ~26 `QuestionRaw` entries.
>     *   **Call 6 (Syllabus):** A single call ingests the syllabus and updates the `SyllabusNode` tree.