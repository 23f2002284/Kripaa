-- PostgreSQL Schema DDL

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ENUMS
CREATE TYPE memory_type AS ENUM ('episodic','semantic','procedural','working');
CREATE TYPE exclusion_reason AS ENUM (
  'redundant_variant','overrepresented_topic','low_confidence_trend',
  'outlier_difficulty','syllabus_mismatch','insufficient_recurrence','composite_superseded'
);
CREATE TYPE model_phase AS ENUM ('ocr','normalization','mapping','trend','prediction','ensemble','report','evaluation');
CREATE TYPE vote_decision AS ENUM ('include','exclude');
CREATE TYPE candidate_status AS ENUM ('pending','selected','excluded');
CREATE TYPE topic_status AS ENUM ('emerging','declining','stable');

-- RAW QUESTIONS
CREATE TABLE questions_raw (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  year INT NOT NULL,
  section TEXT,
  original_numbering TEXT,
  raw_text TEXT NOT NULL,
  marks INT,
  source_pdf TEXT,
  ocr_confidence REAL,
  ingestion_time TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(year, original_numbering, raw_text)
);

CREATE INDEX idx_questions_raw_year ON questions_raw(year);
CREATE INDEX idx_questions_raw_fulltext ON questions_raw USING GIN (to_tsvector('english', raw_text));

-- NORMALIZED QUESTIONS
CREATE TABLE questions_normalized (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  base_form TEXT NOT NULL,
  marks INT,
  difficulty SMALLINT CHECK (difficulty BETWEEN 1 AND 5),
  variant_group_id UUID,
  canonical_hash TEXT NOT NULL,
  original_ids UUID[] NOT NULL,
  placeholders TEXT[] DEFAULT '{}',
  taxonomy TEXT[],
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT fk_variant_group FOREIGN KEY (variant_group_id) REFERENCES variant_groups(id) ON DELETE SET NULL
);

-- Since variant_groups referenced above, define it now:
CREATE TABLE variant_groups (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  canonical_stem TEXT NOT NULL,
  slot_count INT NOT NULL DEFAULT 0,
  recurrence_count INT DEFAULT 0,
  first_year INT,
  last_year INT,
  signature TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(signature)
);

CREATE INDEX idx_variant_groups_signature ON variant_groups(signature);

-- Add foreign key with deferred creation (already done in normalized table constraint)
-- QUESTION PARAMETERS (OPTIONAL granular structure)
CREATE TABLE question_parameters (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  question_id UUID NOT NULL REFERENCES questions_normalized(id) ON DELETE CASCADE,
  placeholder TEXT NOT NULL,
  param_type TEXT,
  range_min REAL,
  range_max REAL,
  notes TEXT,
  UNIQUE(question_id, placeholder)
);

-- SYLLABUS NODES
CREATE TABLE syllabus_nodes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  parent_id UUID REFERENCES syllabus_nodes(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  code TEXT,
  weight REAL DEFAULT 1.0,
  times_asked INT DEFAULT 0,
  last_asked_year INT,
  gap_score REAL DEFAULT 0.0,
  status topic_status DEFAULT 'stable',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(title, parent_id)
);

CREATE INDEX idx_syllabus_nodes_status ON syllabus_nodes(status);

-- QUESTION ↔ TOPIC MAP
CREATE TABLE question_topic_map (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  question_id UUID NOT NULL REFERENCES questions_normalized(id) ON DELETE CASCADE,
  topic_id UUID NOT NULL REFERENCES syllabus_nodes(id) ON DELETE CASCADE,
  relevance_score REAL DEFAULT 1.0,
  source TEXT,
  UNIQUE(question_id, topic_id)
);

CREATE INDEX idx_question_topic_map_topic ON question_topic_map(topic_id);

-- COMPOSITE QUESTIONS
CREATE TABLE composite_questions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title TEXT,
  parts UUID[] NOT NULL, -- references questions_normalized ids
  constructed_stem TEXT,
  marks INT,
  rationale TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- TREND SNAPSHOTS
CREATE TABLE trend_snapshots (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  year_range INT[] NOT NULL,
  topic_stats_json JSONB NOT NULL,
  emerging_topics UUID[] DEFAULT '{}', -- syllabus_nodes ids
  declining_topics UUID[] DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- MODEL RUNS (PROVENANCE)
CREATE TABLE model_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  phase model_phase NOT NULL,
  model_name TEXT NOT NULL,
  model_version TEXT,
  provider TEXT,
  temperature REAL,
  seed INT,
  input_ref UUID, -- optional link to artifact
  output_ref UUID, -- optional link
  parameters_json JSONB,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  finished_at TIMESTAMPTZ,
  duration_ms INT,
  status TEXT,
  notes TEXT
);

CREATE INDEX idx_model_runs_phase ON model_runs(phase);

-- PREDICTION CANDIDATES
CREATE TABLE prediction_candidates (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  normalized_question_id UUID NOT NULL REFERENCES questions_normalized(id) ON DELETE CASCADE,
  trend_snapshot_id UUID REFERENCES trend_snapshots(id) ON DELETE SET NULL,
  scores_json JSONB NOT NULL,
  status candidate_status DEFAULT 'pending',
  generated_by_run UUID REFERENCES model_runs(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_prediction_candidates_status ON prediction_candidates(status);

-- ENSEMBLE VOTES
CREATE TABLE ensemble_votes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  candidate_id UUID NOT NULL REFERENCES prediction_candidates(id) ON DELETE CASCADE,
  model_run_id UUID NOT NULL REFERENCES model_runs(id) ON DELETE CASCADE,
  decision vote_decision NOT NULL,
  confidence REAL,
  rationale TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(candidate_id, model_run_id)
);

-- EXCLUSIONS
CREATE TABLE exclusions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  candidate_id UUID NOT NULL REFERENCES prediction_candidates(id) ON DELETE CASCADE,
  reason exclusion_reason NOT NULL,
  rationale TEXT,
  model_run_id UUID REFERENCES model_runs(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(candidate_id, reason)
);

-- SAMPLE PAPERS
CREATE TABLE sample_papers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  version INT NOT NULL,
  generation_timestamp TIMESTAMPTZ DEFAULT NOW(),
  total_marks INT,
  coverage_metrics_json JSONB,
  built_by_run UUID REFERENCES model_runs(id) ON DELETE SET NULL,
  locked BOOLEAN DEFAULT TRUE,
  UNIQUE(version)
);

-- SAMPLE PAPER ITEMS
CREATE TABLE sample_paper_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  paper_id UUID NOT NULL REFERENCES sample_papers(id) ON DELETE CASCADE,
  candidate_id UUID REFERENCES prediction_candidates(id) ON DELETE SET NULL,
  composite_question_id UUID REFERENCES composite_questions(id) ON DELETE SET NULL,
  ordering INT NOT NULL,
  marks INT,
  origin_type TEXT, -- past_year / syllabus_gap / composite / other
  source_year INT,
  notes TEXT,
  UNIQUE(paper_id, ordering)
);

-- MEMORY ARTIFACTS
CREATE TABLE memory_artifacts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  type memory_type NOT NULL,
  title TEXT,
  content_json JSONB NOT NULL,
  source_refs UUID[] DEFAULT '{}',
  lineage UUID[] DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  hash TEXT,
  version INT DEFAULT 1
);

CREATE INDEX idx_memory_artifacts_type ON memory_artifacts(type);

-- PROVENANCE LINKS (generic graph)
CREATE TABLE provenance_links (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_id UUID NOT NULL,
  target_id UUID NOT NULL,
  relation TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(source_id, target_id, relation)
);

-- EVALUATION RESULTS
CREATE TABLE evaluation_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  model_run_id UUID REFERENCES model_runs(id) ON DELETE SET NULL,
  context_years INT[] NOT NULL,
  target_year INT,
  metrics_json JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Helpful partial index examples
CREATE INDEX idx_prediction_candidates_selected ON prediction_candidates(id) WHERE status = 'selected';
CREATE INDEX idx_exclusions_reason ON exclusions(reason);