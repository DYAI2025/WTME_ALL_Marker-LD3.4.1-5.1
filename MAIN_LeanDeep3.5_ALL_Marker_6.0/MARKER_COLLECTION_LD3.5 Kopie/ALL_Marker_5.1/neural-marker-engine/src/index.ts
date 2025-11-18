/**
 * Neural Marker Engine - Main Export
 */

export * from './types/marker.types.js';
export * from './engine/marker-engine.js';
export * from './engine/neural-validator.js';
export * from './utils/yaml-parser.js';

import { MarkerEngine } from './engine/marker-engine.js';
import { NeuralValidator, MockNeuralValidator } from './engine/neural-validator.js';
import { EngineConfig } from './types/marker.types.js';

/**
 * Factory function to create a fully configured engine
 */
export function createMarkerEngine(config: Partial<EngineConfig>): MarkerEngine {
  const defaultConfig: EngineConfig = {
    enable_neural_validation: false,
    validation_threshold: 0.6,
    enable_caching: true,
    cache_ttl_seconds: 3600,
    batch_size: 20,
    supabase_url: config.supabase_url || '',
    supabase_key: config.supabase_key || '',
    ...config,
  };

  return new MarkerEngine(defaultConfig);
}

/**
 * Factory function to create a neural validator
 */
export function createNeuralValidator(
  url: string,
  threshold?: number,
  useMock: boolean = false
): NeuralValidator {
  if (useMock) {
    return new MockNeuralValidator(threshold);
  }
  return new NeuralValidator(url, threshold);
}

/**
 * Quick start: Create engine with neural validation
 */
export async function createNeuralMarkerEngine(
  supabaseUrl: string,
  supabaseKey: string,
  neuralValidatorUrl?: string
): Promise<MarkerEngine> {
  const engine = createMarkerEngine({
    supabase_url: supabaseUrl,
    supabase_key: supabaseKey,
    enable_neural_validation: !!neuralValidatorUrl,
    neural_validator_url: neuralValidatorUrl,
  });

  await engine.initialize();
  return engine;
}
