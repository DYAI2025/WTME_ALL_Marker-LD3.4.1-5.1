-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Markers table: stores all marker definitions from YAML
CREATE TABLE IF NOT EXISTS markers (
  id TEXT PRIMARY KEY,
  category TEXT NOT NULL CHECK (category IN ('ATOMIC', 'SEMANTIC', 'CLUSTER', 'META')),
  version TEXT NOT NULL,
  lang TEXT NOT NULL CHECK (lang IN ('de', 'en', 'multi')),
  definition JSONB NOT NULL,
  embedding vector(384), -- Sentence embedding for semantic search (all-MiniLM-L6-v2)
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_markers_category ON markers(category);
CREATE INDEX IF NOT EXISTS idx_markers_lang ON markers(lang);
CREATE INDEX IF NOT EXISTS idx_markers_updated_at ON markers(updated_at DESC);

-- Vector similarity index for semantic search
CREATE INDEX IF NOT EXISTS idx_markers_embedding ON markers
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Model weights table: stores neural model parameters
CREATE TABLE IF NOT EXISTS model_weights (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  model_type TEXT NOT NULL, -- 'validator', 'predictor_escalation', 'predictor_intervention', etc.
  version TEXT NOT NULL,
  architecture TEXT NOT NULL, -- 'distilbert', 'minilm', 'lstm', etc.
  weights_url TEXT, -- URL to model file in storage
  metadata JSONB, -- Training info, metrics, hyperparameters
  is_active BOOLEAN DEFAULT FALSE, -- Only one active version per model_type
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(model_type, version)
);

CREATE INDEX IF NOT EXISTS idx_model_weights_active ON model_weights(model_type, is_active) WHERE is_active = TRUE;

-- Marker events table: real-time stream of detections
CREATE TABLE IF NOT EXISTS marker_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID NOT NULL, -- Groups messages from same conversation
  marker_id TEXT NOT NULL REFERENCES markers(id) ON DELETE CASCADE,
  confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  validated BOOLEAN, -- NULL = pending validation, TRUE/FALSE after neural check
  validation_confidence REAL CHECK (validation_confidence IS NULL OR (validation_confidence >= 0 AND validation_confidence <= 1)),
  context_hash TEXT, -- Anonymized hash of conversation context
  metadata JSONB, -- matched_text, position, etc.
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_marker_events_session ON marker_events(session_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_marker_events_marker ON marker_events(marker_id);
CREATE INDEX IF NOT EXISTS idx_marker_events_validated ON marker_events(validated) WHERE validated IS NULL;

-- Enable realtime for live marker detection streams
ALTER PUBLICATION supabase_realtime ADD TABLE marker_events;

-- Cluster centroids table: discovered patterns from unsupervised learning
CREATE TABLE IF NOT EXISTS cluster_centroids (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID, -- NULL for global patterns, set for user-specific
  cluster_type TEXT NOT NULL, -- 'conversation_archetype', 'ato_candidate', 'context_rule', etc.
  centroid vector(384), -- Embedding centroid
  description TEXT, -- Human-readable summary
  frequency INTEGER DEFAULT 0, -- How often this pattern appears
  examples JSONB, -- Sample conversations/messages
  confidence REAL, -- Quality score for this cluster
  discovered_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cluster_user ON cluster_centroids(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_cluster_type ON cluster_centroids(cluster_type);
CREATE INDEX IF NOT EXISTS idx_cluster_centroid ON cluster_centroids
USING ivfflat (centroid vector_cosine_ops)
WITH (lists = 50);

-- Conversation sessions table: metadata about conversations
CREATE TABLE IF NOT EXISTS conversation_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID, -- Optional: link to user
  metadata JSONB, -- Context, tags, etc.
  started_at TIMESTAMPTZ DEFAULT NOW(),
  ended_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON conversation_sessions(user_id) WHERE user_id IS NOT NULL;

-- Feedback table: user corrections for model training
CREATE TABLE IF NOT EXISTS detection_feedback (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_id UUID REFERENCES marker_events(id) ON DELETE CASCADE,
  feedback_type TEXT NOT NULL CHECK (feedback_type IN ('correct', 'false_positive', 'false_negative', 'context_needed')),
  corrected_marker_id TEXT, -- If user provides correct marker
  notes TEXT,
  context_hash TEXT, -- For privacy-preserving federated learning
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_event ON detection_feedback(event_id);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON detection_feedback(feedback_type);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER update_markers_updated_at
  BEFORE UPDATE ON markers
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Function to ensure only one active model per type
CREATE OR REPLACE FUNCTION ensure_single_active_model()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.is_active = TRUE THEN
    UPDATE model_weights
    SET is_active = FALSE
    WHERE model_type = NEW.model_type
      AND id != NEW.id
      AND is_active = TRUE;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_single_active_model
  BEFORE INSERT OR UPDATE ON model_weights
  FOR EACH ROW
  WHEN (NEW.is_active = TRUE)
  EXECUTE FUNCTION ensure_single_active_model();

-- RLS (Row Level Security) policies
ALTER TABLE markers ENABLE ROW LEVEL SECURITY;
ALTER TABLE marker_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE cluster_centroids ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE detection_feedback ENABLE ROW LEVEL SECURITY;

-- Public read access to markers (they're not sensitive)
CREATE POLICY "Markers are publicly readable" ON markers
  FOR SELECT USING (true);

-- Only authenticated users can write markers (for admin/migration scripts)
CREATE POLICY "Authenticated users can insert markers" ON markers
  FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can update markers" ON markers
  FOR UPDATE USING (auth.role() = 'authenticated');

-- Marker events: users can only see their own sessions
CREATE POLICY "Users can read their own marker events" ON marker_events
  FOR SELECT USING (
    session_id IN (
      SELECT id FROM conversation_sessions
      WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert their own marker events" ON marker_events
  FOR INSERT WITH CHECK (
    session_id IN (
      SELECT id FROM conversation_sessions
      WHERE user_id = auth.uid()
    )
  );

-- Cluster centroids: users can see global patterns and their own
CREATE POLICY "Users can read cluster centroids" ON cluster_centroids
  FOR SELECT USING (
    user_id IS NULL OR user_id = auth.uid()
  );

CREATE POLICY "Users can insert their own clusters" ON cluster_centroids
  FOR INSERT WITH CHECK (user_id = auth.uid());

-- Conversation sessions: users can only access their own
CREATE POLICY "Users can read their own sessions" ON conversation_sessions
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own sessions" ON conversation_sessions
  FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own sessions" ON conversation_sessions
  FOR UPDATE USING (user_id = auth.uid());

-- Feedback: users can provide feedback on their own detections
CREATE POLICY "Users can read their own feedback" ON detection_feedback
  FOR SELECT USING (
    event_id IN (
      SELECT me.id FROM marker_events me
      JOIN conversation_sessions cs ON me.session_id = cs.id
      WHERE cs.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert their own feedback" ON detection_feedback
  FOR INSERT WITH CHECK (
    event_id IN (
      SELECT me.id FROM marker_events me
      JOIN conversation_sessions cs ON me.session_id = cs.id
      WHERE cs.user_id = auth.uid()
    )
  );

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON markers TO anon, authenticated;
GRANT ALL ON marker_events TO authenticated;
GRANT ALL ON cluster_centroids TO authenticated;
GRANT ALL ON conversation_sessions TO authenticated;
GRANT ALL ON detection_feedback TO authenticated;
