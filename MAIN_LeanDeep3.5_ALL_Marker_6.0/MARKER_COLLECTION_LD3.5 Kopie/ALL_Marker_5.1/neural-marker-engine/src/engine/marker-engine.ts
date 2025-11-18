import { createClient, SupabaseClient } from '@supabase/supabase-js';
import {
  Marker,
  AtomicMarker,
  SemanticMarker,
  ClusterMarker,
  MetaMarker,
  Message,
  Detection,
  EngineConfig,
  MarkerRow,
} from '../types/marker.types.js';

/**
 * Main marker detection engine
 */
export class MarkerEngine {
  private supabase: SupabaseClient;
  private config: EngineConfig;
  private markersCache: Map<string, Marker> = new Map();
  private cacheExpiry: number = 0;

  constructor(config: EngineConfig) {
    this.config = config;
    this.supabase = createClient(config.supabase_url, config.supabase_key);
  }

  /**
   * Initialize engine by loading markers from database
   */
  async initialize(): Promise<void> {
    console.log('Initializing marker engine...');
    await this.loadMarkers();
    console.log(`Loaded ${this.markersCache.size} markers`);
  }

  /**
   * Load markers from Supabase (with caching)
   */
  private async loadMarkers(forceRefresh: boolean = false): Promise<void> {
    const now = Date.now();

    // Check cache validity
    if (!forceRefresh && this.cacheExpiry > now && this.markersCache.size > 0) {
      return; // Cache still valid
    }

    // Fetch from database
    const { data, error } = await this.supabase
      .from('markers')
      .select('*')
      .returns<MarkerRow[]>();

    if (error) {
      throw new Error(`Failed to load markers: ${error.message}`);
    }

    // Clear and rebuild cache
    this.markersCache.clear();
    data?.forEach((row) => {
      this.markersCache.set(row.id, row.definition);
    });

    // Set cache expiry
    this.cacheExpiry = now + this.config.cache_ttl_seconds * 1000;
  }

  /**
   * Get a marker by ID
   */
  getMarker(id: string): Marker | undefined {
    return this.markersCache.get(id);
  }

  /**
   * Get all markers of a specific category
   */
  getMarkersByCategory(category: string): Marker[] {
    return Array.from(this.markersCache.values()).filter(
      (m) => m.category === category
    );
  }

  /**
   * Detect markers in a single message
   */
  detectInMessage(message: Message): Detection[] {
    const detections: Detection[] = [];

    // Run ATOMIC markers first
    const atomicMarkers = this.getMarkersByCategory('ATOMIC') as AtomicMarker[];
    for (const marker of atomicMarkers) {
      const atomicDetections = this.detectAtomic(marker, message);
      detections.push(...atomicDetections);
    }

    return detections;
  }

  /**
   * Detect markers in a conversation (with context)
   */
  async detectInConversation(messages: Message[]): Promise<Detection[]> {
    const allDetections: Detection[] = [];

    // 1. Detect ATOMIC markers in each message
    const atomicDetectionsByMessage = new Map<string, Detection[]>();
    for (const message of messages) {
      const detections = this.detectInMessage(message);
      atomicDetectionsByMessage.set(message.id, detections);
      allDetections.push(...detections);
    }

    // 2. Detect SEMANTIC markers (require multiple ATOs in context)
    const semanticDetections = this.detectSemantic(
      messages,
      atomicDetectionsByMessage
    );
    allDetections.push(...semanticDetections);

    // 3. Detect CLUSTER markers (patterns over message windows)
    const clusterDetections = this.detectCluster(
      messages,
      allDetections
    );
    allDetections.push(...clusterDetections);

    // 4. Detect META markers (high-level patterns)
    const metaDetections = this.detectMeta(
      messages,
      allDetections
    );
    allDetections.push(...metaDetections);

    return allDetections;
  }

  /**
   * Detect ATOMIC markers using regex patterns
   */
  private detectAtomic(marker: AtomicMarker, message: Message): Detection[] {
    const detections: Detection[] = [];

    if (!marker.pattern || marker.pattern.length === 0) {
      return detections;
    }

    for (const patternStr of marker.pattern) {
      try {
        const regex = new RegExp(patternStr, 'g');
        const matches = Array.from(message.text.matchAll(regex));

        for (const match of matches) {
          detections.push({
            marker_id: marker.id,
            category: 'ATOMIC',
            confidence: 1.0, // Rule-based = certain
            matched_text: match[0],
            matched_patterns: [patternStr],
            position: {
              start: match.index || 0,
              end: (match.index || 0) + match[0].length,
            },
            timestamp: message.timestamp,
          });
        }
      } catch (error) {
        console.warn(`Invalid regex in ${marker.id}: ${patternStr}`);
      }
    }

    return detections;
  }

  /**
   * Detect SEMANTIC markers (combinations of ATOs)
   */
  private detectSemantic(
    messages: Message[],
    atomicDetections: Map<string, Detection[]>
  ): Detection[] {
    const detections: Detection[] = [];
    const semanticMarkers = this.getMarkersByCategory('SEMANTIC') as SemanticMarker[];

    for (const marker of semanticMarkers) {
      const detection = this.evaluateSemantic(
        marker,
        messages,
        atomicDetections
      );
      if (detection) {
        detections.push(detection);
      }
    }

    return detections;
  }

  /**
   * Evaluate a SEMANTIC marker activation
   */
  private evaluateSemantic(
    marker: SemanticMarker,
    messages: Message[],
    atomicDetections: Map<string, Detection[]>
  ): Detection | null {
    const requiredMarkers = marker.composed_of || [];
    if (requiredMarkers.length === 0) return null;

    // Parse activation logic (e.g., "ANY 2 IN 3 messages")
    const windowSize = this.parseWindowSize(marker.activation_logic || 'ANY 2');
    const requiredCount = this.parseRequiredCount(marker.activation_logic || 'ANY 2');

    // Check last N messages
    const recentMessages = messages.slice(-windowSize);
    const foundMarkers = new Set<string>();

    for (const message of recentMessages) {
      const msgDetections = atomicDetections.get(message.id) || [];
      msgDetections.forEach((d) => {
        if (requiredMarkers.includes(d.marker_id)) {
          foundMarkers.add(d.marker_id);
        }
      });
    }

    // Check if activation threshold met
    if (foundMarkers.size >= requiredCount) {
      return {
        marker_id: marker.id,
        category: 'SEMANTIC',
        confidence: this.calculateSemanticConfidence(marker, foundMarkers.size),
        matched_patterns: Array.from(foundMarkers),
        timestamp: messages[messages.length - 1].timestamp,
      };
    }

    return null;
  }

  /**
   * Detect CLUSTER markers (temporal patterns)
   */
  private detectCluster(
    messages: Message[],
    allDetections: Detection[]
  ): Detection[] {
    const detections: Detection[] = [];
    const clusterMarkers = this.getMarkersByCategory('CLUSTER') as ClusterMarker[];

    for (const marker of clusterMarkers) {
      const detection = this.evaluateCluster(marker, messages, allDetections);
      if (detection) {
        detections.push(detection);
      }
    }

    return detections;
  }

  /**
   * Evaluate a CLUSTER marker activation
   */
  private evaluateCluster(
    marker: ClusterMarker,
    messages: Message[],
    allDetections: Detection[]
  ): Detection | null {
    const windowSize = marker.window?.messages || 50;
    const recentMessages = messages.slice(-windowSize);
    const recentMsgIds = new Set(recentMessages.map((m) => m.id));

    // Get detections within window
    const windowDetections = allDetections.filter((d) =>
      recentMessages.some((m) => m.timestamp === d.timestamp)
    );

    // Check components
    let components: string[] = [];
    if (marker.composed_of) {
      components = marker.composed_of.flatMap((c) => c.marker_ids);
    } else if (marker.components) {
      components = marker.components;
    }

    if (components.length === 0) return null;

    // Count distinct component detections
    const foundComponents = new Set<string>();
    windowDetections.forEach((d) => {
      if (components.includes(d.marker_id)) {
        foundComponents.add(d.marker_id);
      }
    });

    // Parse activation rule (e.g., "AT_LEAST 2 DISTINCT SEMs IN 24 messages")
    const requiredCount = this.parseRequiredCount(marker.activation?.rule || 'AT_LEAST 2');

    if (foundComponents.size >= requiredCount) {
      return {
        marker_id: marker.id,
        category: 'CLUSTER',
        confidence: this.calculateClusterConfidence(
          marker,
          foundComponents.size,
          windowDetections.length
        ),
        matched_patterns: Array.from(foundComponents),
        timestamp: messages[messages.length - 1].timestamp,
      };
    }

    return null;
  }

  /**
   * Detect META markers (high-level patterns)
   */
  private detectMeta(
    messages: Message[],
    allDetections: Detection[]
  ): Detection[] {
    const detections: Detection[] = [];
    const metaMarkers = this.getMarkersByCategory('META') as MetaMarker[];

    for (const marker of metaMarkers) {
      const detection = this.evaluateMeta(marker, messages, allDetections);
      if (detection) {
        detections.push(detection);
      }
    }

    return detections;
  }

  /**
   * Evaluate a META marker activation
   */
  private evaluateMeta(
    marker: MetaMarker,
    messages: Message[],
    allDetections: Detection[]
  ): Detection | null {
    const requiredComponents = marker.components || [];
    if (requiredComponents.length === 0) return null;

    // Check if all required components are present in detections
    const foundComponents = new Set<string>();
    allDetections.forEach((d) => {
      if (requiredComponents.includes(d.marker_id)) {
        foundComponents.add(d.marker_id);
      }
    });

    // META markers typically require most/all components
    const threshold = Math.ceil(requiredComponents.length * 0.6); // 60% threshold

    if (foundComponents.size >= threshold) {
      return {
        marker_id: marker.id,
        category: 'META',
        confidence: foundComponents.size / requiredComponents.length,
        matched_patterns: Array.from(foundComponents),
        timestamp: messages[messages.length - 1].timestamp,
      };
    }

    return null;
  }

  /**
   * Parse window size from activation logic string
   */
  private parseWindowSize(logic: string): number {
    const match = logic.match(/IN (\d+) messages?/i);
    return match ? parseInt(match[1], 10) : 3;
  }

  /**
   * Parse required count from activation logic string
   */
  private parseRequiredCount(logic: string): number {
    // Handle patterns like "ANY 2", "AT_LEAST 2", "ALL"
    if (logic.includes('ALL')) return 999; // Requires all components

    const match = logic.match(/(\d+)/);
    return match ? parseInt(match[1], 10) : 2;
  }

  /**
   * Calculate confidence for SEMANTIC markers
   */
  private calculateSemanticConfidence(
    marker: SemanticMarker,
    foundCount: number
  ): number {
    const base = marker.scoring?.base || 1.0;
    const weight = marker.scoring?.weight || 1.0;

    // Confidence increases with more components found
    const ratio = foundCount / (marker.composed_of?.length || 1);
    return Math.min(base * weight * ratio, 1.0);
  }

  /**
   * Calculate confidence for CLUSTER markers
   */
  private calculateClusterConfidence(
    marker: ClusterMarker,
    distinctCount: number,
    totalDetections: number
  ): number {
    const base = marker.scoring?.base || 1.0;
    const weight = marker.scoring?.weight || 1.0;
    const decay = marker.scoring?.decay || 0;

    // Consider both distinct components and frequency
    const distinctScore = distinctCount / 10; // Normalize
    const frequencyScore = Math.log(totalDetections + 1) / 5; // Log scale

    let confidence = base * weight * (distinctScore + frequencyScore) / 2;

    // Apply decay if configured
    if (decay > 0) {
      confidence *= 1 - decay;
    }

    return Math.min(confidence, 1.0);
  }

  /**
   * Refresh marker cache
   */
  async refreshMarkers(): Promise<void> {
    await this.loadMarkers(true);
  }
}
