import {
  Message,
  Detection,
  ValidationRequest,
  ValidationResponse,
} from '../types/marker.types.js';

/**
 * Neural validator client for validating rule-based detections
 */
export class NeuralValidator {
  private validatorUrl: string;
  private threshold: number;
  private enabled: boolean;

  constructor(
    validatorUrl: string,
    threshold: number = 0.6,
    enabled: boolean = true
  ) {
    this.validatorUrl = validatorUrl;
    this.threshold = threshold;
    this.enabled = enabled;
  }

  /**
   * Validate detections using neural model
   */
  async validate(
    context: Message[],
    candidates: Detection[]
  ): Promise<ValidationResponse> {
    const startTime = Date.now();

    // If neural validation disabled, pass through all candidates
    if (!this.enabled) {
      return {
        validated: candidates.map((c) => ({
          ...c,
          validated: true,
          validation_confidence: 1.0,
        })),
        processing_time_ms: 0,
      };
    }

    try {
      const request: ValidationRequest = {
        context: context.slice(-10), // Last 10 messages for context
        candidates,
        options: {
          threshold: this.threshold,
          return_all: true,
        },
      };

      const response = await fetch(this.validatorUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Validation failed: ${response.statusText}`);
      }

      const result = await response.json();
      const processingTime = Date.now() - startTime;

      return {
        validated: result.validated || [],
        rejected: result.rejected || [],
        processing_time_ms: processingTime,
      };
    } catch (error) {
      console.error('Neural validation error:', error);

      // Fallback: accept all candidates if neural service fails
      return {
        validated: candidates.map((c) => ({
          ...c,
          validated: true,
          validation_confidence: 0.5, // Indicate uncertainty
        })),
        rejected: [],
        processing_time_ms: Date.now() - startTime,
      };
    }
  }

  /**
   * Validate a single detection
   */
  async validateSingle(
    context: Message[],
    candidate: Detection
  ): Promise<Detection> {
    const result = await this.validate(context, [candidate]);
    return result.validated[0] || candidate;
  }

  /**
   * Batch validate multiple detections (more efficient)
   */
  async validateBatch(
    context: Message[],
    candidates: Detection[],
    batchSize: number = 20
  ): Promise<ValidationResponse> {
    const batches: Detection[][] = [];

    // Split into batches
    for (let i = 0; i < candidates.length; i += batchSize) {
      batches.push(candidates.slice(i, i + batchSize));
    }

    // Process batches in parallel
    const results = await Promise.all(
      batches.map((batch) => this.validate(context, batch))
    );

    // Merge results
    const validated: Detection[] = [];
    const rejected: Detection[] = [];
    let totalTime = 0;

    results.forEach((result) => {
      validated.push(...result.validated);
      if (result.rejected) {
        rejected.push(...result.rejected);
      }
      totalTime = Math.max(totalTime, result.processing_time_ms);
    });

    return {
      validated,
      rejected,
      processing_time_ms: totalTime,
    };
  }

  /**
   * Enable/disable neural validation
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  /**
   * Update validation threshold
   */
  setThreshold(threshold: number): void {
    this.threshold = Math.max(0, Math.min(1, threshold));
  }

  /**
   * Check if validator is available
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.validatorUrl}/health`, {
        method: 'GET',
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

/**
 * Mock neural validator for testing (simulates validation without actual model)
 */
export class MockNeuralValidator extends NeuralValidator {
  constructor(threshold: number = 0.6) {
    super('http://localhost:9999/mock', threshold, true);
  }

  async validate(
    context: Message[],
    candidates: Detection[]
  ): Promise<ValidationResponse> {
    const startTime = Date.now();

    // Simple mock logic: reject detections with very short matched text
    const validated: Detection[] = [];
    const rejected: Detection[] = [];

    for (const candidate of candidates) {
      // Mock validation logic
      const mockConfidence = this.mockValidationScore(candidate, context);

      if (mockConfidence >= this.threshold) {
        validated.push({
          ...candidate,
          validated: true,
          validation_confidence: mockConfidence,
        });
      } else {
        rejected.push({
          ...candidate,
          validated: false,
          validation_confidence: mockConfidence,
        });
      }
    }

    return {
      validated,
      rejected,
      processing_time_ms: Date.now() - startTime,
    };
  }

  /**
   * Mock validation scoring
   */
  private mockValidationScore(candidate: Detection, context: Message[]): number {
    // Simple heuristics for mock validation
    let score = 0.7; // Base score

    // Longer matched text = higher confidence
    if (candidate.matched_text) {
      const wordCount = candidate.matched_text.split(/\s+/).length;
      score += Math.min(wordCount * 0.05, 0.2);
    }

    // More context messages = higher confidence
    score += Math.min(context.length * 0.01, 0.1);

    // Add some randomness to simulate neural uncertainty
    score += (Math.random() - 0.5) * 0.1;

    return Math.max(0, Math.min(1, score));
  }
}
