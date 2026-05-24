PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS raw_feedback (
    feedback_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    issue_id TEXT,
    comment_id TEXT,
    title TEXT,
    body TEXT,
    labels TEXT,
    state TEXT,
    author TEXT,
    created_at TEXT,
    updated_at TEXT,
    comments_count INTEGER DEFAULT 0,
    url TEXT,
    fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_raw_feedback_repo ON raw_feedback(repo_name);
CREATE INDEX IF NOT EXISTS idx_raw_feedback_issue ON raw_feedback(issue_id);
CREATE INDEX IF NOT EXISTS idx_raw_feedback_created_at ON raw_feedback(created_at);

CREATE TABLE IF NOT EXISTS cleaned_feedback (
    cleaned_id TEXT PRIMARY KEY,
    feedback_id TEXT NOT NULL,
    cleaned_text TEXT NOT NULL,
    language TEXT,
    feedback_type TEXT,
    duplicate_flag INTEGER DEFAULT 0,
    noise_flag INTEGER DEFAULT 0,
    cleaned_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feedback_id) REFERENCES raw_feedback(feedback_id)
);

CREATE INDEX IF NOT EXISTS idx_cleaned_feedback_feedback_id ON cleaned_feedback(feedback_id);
CREATE INDEX IF NOT EXISTS idx_cleaned_feedback_type ON cleaned_feedback(feedback_type);

CREATE TABLE IF NOT EXISTS feedback_topics (
    topic_id TEXT PRIMARY KEY,
    feedback_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    sentiment TEXT,
    severity INTEGER,
    evidence_quote TEXT,
    confidence REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feedback_id) REFERENCES raw_feedback(feedback_id)
);

CREATE INDEX IF NOT EXISTS idx_feedback_topics_feedback_id ON feedback_topics(feedback_id);
CREATE INDEX IF NOT EXISTS idx_feedback_topics_topic ON feedback_topics(topic);

CREATE TABLE IF NOT EXISTS pain_points (
    pain_point_id TEXT PRIMARY KEY,
    topic_id TEXT,
    user_pain TEXT NOT NULL,
    user_need TEXT,
    evidence_count INTEGER DEFAULT 0,
    priority_hint TEXT,
    related_feedback_ids TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES feedback_topics(topic_id)
);

CREATE TABLE IF NOT EXISTS competitor_features (
    competitor_id TEXT,
    competitor_name TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    feature_category TEXT,
    coverage TEXT,
    strength TEXT,
    weakness TEXT,
    source_url TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (competitor_name, feature_name)
);

CREATE TABLE IF NOT EXISTS opportunity_scores (
    opportunity_id TEXT PRIMARY KEY,
    pain_point_ids TEXT,
    opportunity_name TEXT NOT NULL,
    user_value REAL,
    business_value REAL,
    frequency REAL,
    severity REAL,
    effort REAL,
    risk REAL,
    ai_feasibility REAL,
    evidence_strength REAL,
    priority_score REAL,
    priority TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_opportunity_scores_priority ON opportunity_scores(priority);

CREATE TABLE IF NOT EXISTS prd_drafts (
    prd_id TEXT PRIMARY KEY,
    opportunity_id TEXT,
    title TEXT NOT NULL,
    background TEXT,
    user_story TEXT,
    requirements TEXT,
    non_functional_requirements TEXT,
    acceptance_criteria TEXT,
    metrics TEXT,
    risks TEXT,
    evidence_refs TEXT,
    status TEXT DEFAULT 'draft',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunity_id) REFERENCES opportunity_scores(opportunity_id)
);

CREATE INDEX IF NOT EXISTS idx_prd_drafts_opportunity_id ON prd_drafts(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_prd_drafts_status ON prd_drafts(status);

CREATE TABLE IF NOT EXISTS ai_evaluation_results (
    evaluation_id TEXT PRIMARY KEY,
    output_id TEXT NOT NULL,
    output_type TEXT NOT NULL,
    relevance REAL,
    accuracy REAL,
    actionability REAL,
    evidence_coverage REAL,
    hallucination_risk TEXT,
    human_edit_rate REAL,
    prd_completeness REAL,
    overall_score REAL,
    evaluation_notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_eval_output ON ai_evaluation_results(output_id, output_type);
CREATE INDEX IF NOT EXISTS idx_ai_eval_risk ON ai_evaluation_results(hallucination_risk);

CREATE TABLE IF NOT EXISTS bi_metrics_daily (
    metric_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    product_area TEXT,
    repo_name TEXT,
    dimension TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bi_metrics_name_date ON bi_metrics_daily(metric_name, date);
CREATE INDEX IF NOT EXISTS idx_bi_metrics_repo ON bi_metrics_daily(repo_name);

