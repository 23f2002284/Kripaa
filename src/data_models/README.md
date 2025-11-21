Define Canonical Data Model (Question, VariantGroup, Topic, SyllabusNode, TrendSnapshot).

Entities:

QuestionRaw(id, year, text, marks, section, source_pdf)
QuestionNormalized(id, base_form, parameter_slots[], marks, taxonomy[], difficulty_estimate, variant_group_id)
VariantGroup(id, canonical_stem, numeric_pattern_signature, recurrence_count)
SyllabusNode(id, title, parent_id, weight, last_asked_year, times_asked, gap_score)
TrendSnapshot(id, year_range, topic_stats[], recurrence_matrix, emerging_topics[], declining_topics[])
PredictionCandidate(id, normalized_question_id, confidence_scores {trend, syllabus_gap, ensemble_agreement}, exclusion_reason?)
SamplePaper(id, version, total_marks, questions[], coverage_metrics)
MemoryArtifact(id, type {episodic, semantic, procedural}, content, source_refs[], created_at, lineage[])
Memory Types (Adopt Cognitive Metaphor):

Episodic: Individual past paper contexts.
Semantic: Consolidated trends & taxonomies.
Procedural: Pipeline recipes, prompt templates.
Working: Current prediction session transient context.