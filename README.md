# **PROJECT SUMMARY STEPS (CLEAN, EXECUTABLE, FUTURE-PROOF)**

**Goal:**
Given **Syllabus + PYQs**, create

1. A **70–80% correct predicted sample paper**, and
2. A **detailed reasoning report** (trends, patterns, what-was-excluded, tips, etc.)
   using **OCR + memory + multi-model evaluation**.

---

# **1. INPUT PIPELINE**

### **1.1 OCR + Redaction**

* OCR scan all question papers consistently.
* Normalize formatting.
* Store each question with:

  * Year
  * Marks
  * Topic
  * Syllabus mapping
  * Variants (same Q asked in different forms)

### **1.2 Syllabus Integration**

* Convert syllabus into hierarchical structure:

  * Unit → Subunit → Topic → Subtopic
* Mark which topics appeared, how often, which marks.

---

# **2. MEMORY + CONTEXT SYSTEM**

You need long-term reasoning. This part decides your predictions, not the LLM hallucinations.

### **2.1 Memory Tasks**

* Extract important features: trends, repeated questions, repeated patterns.
* Consolidate into compressed memories:

  * Past paper trends
  * Syllabus coverage trend
  * Important but untouched topics
  * Likely numerical/repeat-style patterns

### **2.2 Memory Provenance**

* Keep all updates with timestamp and reasoning (debug + transparency).
* Tag memories as:

  * “Statistical trend”
  * “Syllabus gap”
  * “Examiner pattern”
  * “Cross-paper similarity”

### **2.3 System + Conversation Memory**

* Use memory as:

  * Retrieval for final sample paper
  * Evidence for the analysis report
  * Audit trail for evaluation

---

# **3. CORE ANALYSIS ENGINE**

### **3.1 Trend Analysis**

LLM or small models derive:

1. **Repeated Questions**
2. **Repeated Patterns**
3. **Marks Trend for Each Topic**
4. **Probability of Topic Reappearance**
5. **Combined Pattern Generation**

   * (e.g., “calculate i., ii., iii.” type questions evolving over years)
### **3.2 Syllabus Gap Reasoning**

* Identify untouched topics with high likelihood based on pattern.
* Predict new questions from those topics.

### **3.3 Multiple Variations Prediction**

Generate 3–5 sample papers using:

* Multiple LLMs
* Multiple calls of same model
* Cross-comparison vote system

(This avoids “one random model hallucination deciding everything.”)

---

# **4. AGENT WORKFLOW**

This needs **multi-agent**, not one monolithic agent.

### **4.1 Agents**

* **OCR Agent**
* **Trend Analysis Agent**
* **Question Generator Agent**
* **Report Writer Agent**
* **Sample Paper Generator Agent**
* **Evaluation Agent** (judge)

### **4.2 Coordination Layer**

* Use LangGraph or Deep-Agent style topology.
* Each agent writes state → saved as memory → retrieved by the next.

### **4.3 Reasoning Discussions**

Agents debate:

* What goes into final paper
* What stays out (recorded in report)
* Why certain variations are chosen

---

# **5. OUTPUT GENERATION**

## **5.1 Final Sample Paper**

Must be:

* Clean
* Consistent format
* Each question tagged:

  * Source (year / topic / predicted)
  * Marks
* Avoid duplicates (generalize numeric questions)

## **5.2 Analysis Report (PDF/PPT)**

Sections:

1. Exam Paper Trends
2. Important Topics
3. Repeated Questions
4. Syllabus Gaps + Predictions
5. Reasoning for each predicted question
6. Questions excluded + why
7. Tips for scoring
8. Agent reasoning trace (optional, simplified)

Both outputs should maintain **fixed styling** (templates, not ad-hoc layouts).

---

# **6. EVALUATION METRICS (CRITICAL)**

You already hinted at this; I cleaned it up:

### **6.1 Accuracy Against Ground Truth**

* Compare predictions against:

  1. Past papers (minus test year)
  2. Most recent semester paper
  3. Current live semester (future evaluation)

### **6.2 Model Consistency Tests**

* Multi-LLM comparison
* Multi-call consistency (stability metric)
* Architecture-based comparison (4B, 14B, etc.)

### **6.3 Automated Metrics**

* Similarity score between predicted and actual
* Topic coverage score
* Trend correctness score
* Novel prediction precision

### **6.4 Human-in-loop**

* Student feedback UI
* Reviewer panel
* Real-time updates

### **6.5 Logging & Tracing**

* System metrics
* Quality metrics
* Memory updates
* Agent trace

---

# **7. STORAGE + GENERALIZATION DESIGN**

### **7.1 Question Storage Format**

Store generalized formats:

* Replace numbers with variables
* Store multiple past variants under one abstract template
* Tag difficulty, marks, topic, pattern type

### **7.2 Syllabus Trend Prediction**

* Trend of papers
* Trend of question types
* Trend of syllabus coverage
* Identify “high probability untouched topics”

---

# **8. PIPELINE CHECKLIST (PRACTICAL IMPLEMENTATION)**

### **8.1 Stack**

* LangGraph / Deep-Agent
* SuperMemory / Mem0
* Qwen 4B or similar for extraction
* OCR (PaddleOCR / Tesseract)

### **8.2 Context Management**

* Cluster similar questions
* Build compact memories with maximum context
* Unify related syllabus topics
* Generalize numerical questions

### **8.3 Output Module**

* PDF export (Ankaa-style)
* Strict template
* No randomness in formatting

### **8.4 Final Evaluation**

* Run all metrics
* Record everything
* Add to submission report

---

# **9. FINAL DELIVERY**

* **Sample Paper** (clean, justified, structured)
* **Reasoning Report** (detailed, trends, tips, why certain questions were excluded)
* **Submission PDF/PPT**
* **Post Project Plans**: share online, collaborate, communicate, update.

---

## **Core Idea (in my own words):**

You’re building a memory-based, multi-agent exam prediction system that actually behaves like a careful panel of teachers instead of a single overconfident chatbot.

It’s ambitious, but if you implement even 60% of the above, judges will lose their minds.

If you want, I can convert this into:

* a **system architecture diagram**,
* a **module-level design**,
* a **LangGraph graph**, or
* a **GitHub-ready README**.

---

# **10. CURRENT PROGRESS**

### **Implemented Data Models & Agents Structure**

The following data models have been implemented and organized by their respective agents:

*   **OCR Agent**
    *   `QuestionRaw`: Raw extracted question data.

*   **Normalization & Canonicalization Agent**
    *   `QuestionNormalized`: Standardized question format.
    *   `QuestionParameter`: Parameters extracted from questions.
    *   `CompositeQuestion`: Handling complex/multi-part questions.

*   **Syllabus Mapping & Topic Tagging Agent**
    *   `SyllabusNode`: Hierarchical syllabus structure.
    *   `QuestionTopicMap`: Mapping questions to topics.
    *   `TopicStatus`: Status tracking for topics.

*   **Memory Management Agent**
    *   `MemoryArtifact`: Stored memory items.
    *   `MemoryType`: Classification of memories.
    *   `VECTOR_DIM`: Configuration for vector embeddings.

*   **Template Generator Agent**
    *   `VariantGroup`: Grouping similar question variants.

*   **Voting & Ranking Agent**
    *   `EnsembleVote`: Voting mechanism results.
    *   `VoteDecision`: Final decisions from voting.

*   **Pattern & Trend Analysis Agent**
    *   `TrendSnapshot`: Captured trend data.
    *   `PredictionCandidate`: Potential questions for prediction.
    *   `CandidateStatus`: Status of prediction candidates.

*   **Sample Paper Generator Agent**
    *   `SamplePaper`: The generated paper structure.
    *   `SamplePaperItem`: Individual items within the paper.

*   **Reasoning + Report Generation Agent**
    *   `ProvenanceLink`: Tracing the origin of decisions.

*   **Evaluation Agent**
    *   `ModelRun`: Tracking model execution runs.
    *   `EvaluationResult`: Results from evaluation metrics.
    *   `Exclusion`: Records of excluded items.
    *   `ExclusionReason`: Reasons for exclusion.
    *   `ModelPhase`: Phases of the model pipeline.
