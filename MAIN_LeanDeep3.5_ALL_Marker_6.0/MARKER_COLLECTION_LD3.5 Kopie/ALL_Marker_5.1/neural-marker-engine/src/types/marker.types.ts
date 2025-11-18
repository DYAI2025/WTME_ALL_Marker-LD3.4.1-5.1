/**
 * LeanDeep 3.4 Marker Type Definitions
 */

export type MarkerCategory = 'ATOMIC' | 'SEMANTIC' | 'CLUSTER' | 'META';
export type Language = 'de' | 'en' | 'multi';

/**
 * Semantic frame structure (required for all markers)
 */
export interface MarkerFrame {
  signal: string | string[];
  concept: string;
  pragmatics: string;
  narrative: string;
}

/**
 * Activation logic for ATOMIC markers
 */
export type ActivationLogic =
  | 'ANY 1'
  | 'ANY 2'
  | 'ALL'
  | string; // Custom logic like "ANY 2 IN 3 messages"

/**
 * Scoring configuration
 */
export interface ScoringConfig {
  base: number;
  weight: number;
  decay?: number;
  formula?: 'linear' | 'logistic' | 'exponential';
}

/**
 * Window configuration for CLU markers
 */
export interface WindowConfig {
  messages: number;
  time_seconds?: number;
}

/**
 * Activation rules for CLUSTER markers
 */
export interface ActivationRule {
  rule: string; // e.g., "AT_LEAST 2 DISTINCT SEMs IN 24 messages"
  threshold?: number;
}

/**
 * Component reference with optional weight
 */
export interface ComponentReference {
  marker_ids: string[];
  weight: number;
}

/**
 * Repair log entry
 */
export interface RepairLogEntry {
  rule: string;
  note: string;
  date: string;
}

/**
 * Base marker definition (common fields)
 */
export interface BaseMarker {
  id: string;
  schema?: string; // "LeanDeep"
  version?: string; // "3.4"
  schema_version?: string; // Alternative field name
  namespace?: string;
  lang: Language;
  category: MarkerCategory;
  description: string;
  frame: MarkerFrame;
  examples?: string[] | { positive: string[]; negative: string[] };
  tags?: string[];
  metadata?: {
    repair_log?: RepairLogEntry[];
    [key: string]: any;
  };
}

/**
 * ATOMIC marker definition
 */
export interface AtomicMarker extends BaseMarker {
  category: 'ATOMIC';
  pattern: string[]; // Array of regex patterns
  activation_logic?: ActivationLogic;
}

/**
 * SEMANTIC marker definition
 */
export interface SemanticMarker extends BaseMarker {
  category: 'SEMANTIC';
  composed_of: string[]; // Array of marker IDs
  activation_logic?: ActivationLogic;
  scoring?: ScoringConfig;
}

/**
 * CLUSTER marker definition
 */
export interface ClusterMarker extends BaseMarker {
  category: 'CLUSTER';
  composed_of?: ComponentReference[]; // With weights
  components?: string[]; // Alternative field name
  activation?: ActivationRule;
  window?: WindowConfig;
  scoring?: ScoringConfig;
  pattern?: string[]; // Some CLU markers have patterns
}

/**
 * META marker definition
 */
export interface MetaMarker extends BaseMarker {
  category: 'META';
  components: string[]; // Array of marker IDs
  composed_of?: string[]; // Alternative field name
  pattern?: string[]; // Description of meta-pattern
}

/**
 * Union type for all marker types
 */
export type Marker = AtomicMarker | SemanticMarker | ClusterMarker | MetaMarker;

/**
 * Message structure for detection
 */
export interface Message {
  id: string;
  speaker: string;
  text: string;
  timestamp: number; // Unix timestamp
  metadata?: Record<string, any>;
}

/**
 * Detection result
 */
export interface Detection {
  marker_id: string;
  category: MarkerCategory;
  confidence: number; // 0.0 - 1.0 from rule-based engine
  matched_text?: string; // Text that triggered the match
  matched_patterns?: string[]; // Which patterns matched
  position?: { start: number; end: number }; // Position in text
  validated?: boolean; // Set by neural validator
  validation_confidence?: number; // Neural validator confidence
  timestamp: number;
}

/**
 * Conversation context for neural validation
 */
export interface ConversationContext {
  messages: Message[];
  window_size?: number; // How many recent messages to include
}

/**
 * Neural validation request
 */
export interface ValidationRequest {
  context: Message[];
  candidates: Detection[];
  options?: {
    threshold?: number; // Minimum confidence to accept (default: 0.6)
    return_all?: boolean; // Return rejected candidates too
  };
}

/**
 * Neural validation response
 */
export interface ValidationResponse {
  validated: Detection[];
  rejected?: Detection[];
  processing_time_ms: number;
}

/**
 * Prediction request
 */
export interface PredictionRequest {
  context: Message[];
  current_detections: Detection[];
  prediction_type: 'next_markers' | 'escalation' | 'trajectory' | 'intervention';
  horizon?: number; // How many messages/seconds to predict ahead
}

/**
 * Prediction response
 */
export interface PredictionResponse {
  prediction_type: string;
  predictions: {
    marker_id?: string;
    probability: number;
    horizon?: number;
    explanation?: string;
  }[];
  escalation_score?: number; // 0.0 - 1.0
  intervention_suggested?: boolean;
  processing_time_ms: number;
}

/**
 * Database schema for markers table
 */
export interface MarkerRow {
  id: string;
  category: MarkerCategory;
  version: string;
  lang: Language;
  definition: Marker; // JSONB
  embedding?: number[]; // Vector embedding for neural search
  updated_at: string;
  created_at: string;
}

/**
 * Database schema for marker_events table
 */
export interface MarkerEventRow {
  id: string;
  session_id: string;
  marker_id: string;
  confidence: number;
  validated: boolean | null;
  context_hash?: string;
  metadata?: Record<string, any>;
  timestamp: string;
}

/**
 * Engine configuration
 */
export interface EngineConfig {
  enable_neural_validation: boolean;
  neural_validator_url?: string;
  validation_threshold: number;
  enable_caching: boolean;
  cache_ttl_seconds: number;
  batch_size: number;
  supabase_url: string;
  supabase_key: string;
}
