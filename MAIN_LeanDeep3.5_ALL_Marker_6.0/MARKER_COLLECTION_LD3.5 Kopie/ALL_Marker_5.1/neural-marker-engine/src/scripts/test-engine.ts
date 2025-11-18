#!/usr/bin/env tsx
import * as dotenv from 'dotenv';
import { MarkerEngine } from '../engine/marker-engine.js';
import { MockNeuralValidator } from '../engine/neural-validator.js';
import { Message, Detection } from '../types/marker.types.js';

dotenv.config();

const SUPABASE_URL = process.env.SUPABASE_URL || '';
const SUPABASE_KEY = process.env.SUPABASE_ANON_KEY || '';

/**
 * Test conversation data
 */
const testConversation: Message[] = [
  {
    id: 'msg1',
    speaker: 'A',
    text: 'Du kommst immer zu spät!',
    timestamp: Date.now() - 10000,
  },
  {
    id: 'msg2',
    speaker: 'B',
    text: 'Das stimmt nicht. Ich versuche mein Bestes.',
    timestamp: Date.now() - 9000,
  },
  {
    id: 'msg3',
    speaker: 'A',
    text: 'Nie hörst du mir zu. Das ist ständig dasselbe.',
    timestamp: Date.now() - 8000,
  },
  {
    id: 'msg4',
    speaker: 'B',
    text: 'Ich höre dir zu, aber du greifst mich immer an.',
    timestamp: Date.now() - 7000,
  },
  {
    id: 'msg5',
    speaker: 'A',
    text: 'Tut mir leid. Ich wollte dich nicht verletzen.',
    timestamp: Date.now() - 6000,
  },
];

const depressionConversation: Message[] = [
  {
    id: 'msg1',
    speaker: 'User',
    text: 'I feel so sad and hopeless every day.',
    timestamp: Date.now() - 5000,
  },
  {
    id: 'msg2',
    speaker: 'User',
    text: 'The pain in my chest won\'t go away.',
    timestamp: Date.now() - 4000,
  },
  {
    id: 'msg3',
    speaker: 'User',
    text: 'I blame myself for everything that went wrong.',
    timestamp: Date.now() - 3000,
  },
  {
    id: 'msg4',
    speaker: 'User',
    text: 'I was happy once, but now everything is meaningless.',
    timestamp: Date.now() - 2000,
  },
];

/**
 * Print detection results in a formatted way
 */
function printDetections(detections: Detection[], title: string): void {
  console.log(`\n${'='.repeat(60)}`);
  console.log(title);
  console.log('='.repeat(60));

  if (detections.length === 0) {
    console.log('No detections found.');
    return;
  }

  // Group by category
  const byCategory: Record<string, Detection[]> = {};
  detections.forEach((d) => {
    if (!byCategory[d.category]) {
      byCategory[d.category] = [];
    }
    byCategory[d.category].push(d);
  });

  // Print each category
  for (const [category, dets] of Object.entries(byCategory)) {
    console.log(`\n${category} (${dets.length}):`);
    console.log('-'.repeat(60));

    dets.forEach((d) => {
      console.log(`  ${d.marker_id}`);
      console.log(`    Confidence: ${d.confidence.toFixed(2)}`);
      if (d.matched_text) {
        console.log(`    Matched: "${d.matched_text}"`);
      }
      if (d.matched_patterns && d.matched_patterns.length > 0) {
        console.log(`    Patterns: ${d.matched_patterns.join(', ')}`);
      }
      if (d.validated !== undefined) {
        console.log(`    Validated: ${d.validated} (${d.validation_confidence?.toFixed(2)})`);
      }
      console.log('');
    });
  }

  console.log(`\nTotal detections: ${detections.length}`);
}

/**
 * Test basic marker detection
 */
async function testBasicDetection(engine: MarkerEngine): Promise<void> {
  console.log('\n🧪 Test 1: Basic Marker Detection');
  console.log('Testing German conversation with absolutist language...\n');

  const detections = await engine.detectInConversation(testConversation);
  printDetections(detections, 'German Conversation Detections');
}

/**
 * Test depression markers
 */
async function testDepressionMarkers(engine: MarkerEngine): Promise<void> {
  console.log('\n🧪 Test 2: Depression Marker Detection');
  console.log('Testing conversation with depressive language...\n');

  const detections = await engine.detectInConversation(depressionConversation);
  printDetections(detections, 'Depression Marker Detections');
}

/**
 * Test neural validation
 */
async function testNeuralValidation(engine: MarkerEngine): Promise<void> {
  console.log('\n🧪 Test 3: Neural Validation (Mock)');
  console.log('Testing neural validator with mock implementation...\n');

  // Get initial detections
  const detections = await engine.detectInConversation(testConversation);
  console.log(`Initial detections: ${detections.length}`);

  // Create mock validator
  const validator = new MockNeuralValidator(0.6);

  // Validate
  const result = await validator.validate(testConversation, detections);

  console.log(`\nValidation Results:`);
  console.log(`  Validated: ${result.validated.length}`);
  console.log(`  Rejected: ${result.rejected?.length || 0}`);
  console.log(`  Processing time: ${result.processing_time_ms}ms`);

  printDetections(result.validated, 'Validated Detections');

  if (result.rejected && result.rejected.length > 0) {
    printDetections(result.rejected, 'Rejected Detections');
  }
}

/**
 * Test marker info retrieval
 */
async function testMarkerInfo(engine: MarkerEngine): Promise<void> {
  console.log('\n🧪 Test 4: Marker Information Retrieval');

  const atomicMarkers = engine.getMarkersByCategory('ATOMIC');
  const semanticMarkers = engine.getMarkersByCategory('SEMANTIC');
  const clusterMarkers = engine.getMarkersByCategory('CLUSTER');
  const metaMarkers = engine.getMarkersByCategory('META');

  console.log('\nMarker counts:');
  console.log(`  ATOMIC:   ${atomicMarkers.length}`);
  console.log(`  SEMANTIC: ${semanticMarkers.length}`);
  console.log(`  CLUSTER:  ${clusterMarkers.length}`);
  console.log(`  META:     ${metaMarkers.length}`);

  // Show example marker
  const exampleMarker = engine.getMarker('ATO_ABSOLUTIZER');
  if (exampleMarker) {
    console.log('\nExample marker (ATO_ABSOLUTIZER):');
    console.log(JSON.stringify(exampleMarker, null, 2));
  }
}

/**
 * Test single message detection
 */
async function testSingleMessage(engine: MarkerEngine): Promise<void> {
  console.log('\n🧪 Test 5: Single Message Detection');

  const message: Message = {
    id: 'test1',
    speaker: 'TestUser',
    text: 'Du bist immer so gemein! Das ist nie anders!',
    timestamp: Date.now(),
  };

  const detections = engine.detectInMessage(message);
  printDetections(detections, 'Single Message Detections');
}

/**
 * Performance benchmark
 */
async function benchmarkDetection(engine: MarkerEngine): Promise<void> {
  console.log('\n🧪 Test 6: Performance Benchmark');

  const iterations = 100;
  const startTime = Date.now();

  for (let i = 0; i < iterations; i++) {
    await engine.detectInConversation(testConversation);
  }

  const endTime = Date.now();
  const totalTime = endTime - startTime;
  const avgTime = totalTime / iterations;

  console.log(`\nBenchmark Results:`);
  console.log(`  Iterations: ${iterations}`);
  console.log(`  Total time: ${totalTime}ms`);
  console.log(`  Average per conversation: ${avgTime.toFixed(2)}ms`);
  console.log(`  Throughput: ${(1000 / avgTime).toFixed(2)} conversations/second`);
}

/**
 * Main test runner
 */
async function main() {
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║        Neural Marker Engine - Test Suite                  ║');
  console.log('╚════════════════════════════════════════════════════════════╝');

  try {
    // Initialize engine
    console.log('\n📦 Initializing marker engine...');

    if (!SUPABASE_URL) {
      console.error('\n❌ Error: SUPABASE_URL not configured in .env');
      console.log('\nFor testing without Supabase, create a mock implementation.');
      process.exit(1);
    }

    const engine = new MarkerEngine({
      supabase_url: SUPABASE_URL,
      supabase_key: SUPABASE_KEY,
      enable_neural_validation: false,
      validation_threshold: 0.6,
      enable_caching: true,
      cache_ttl_seconds: 3600,
      batch_size: 20,
    });

    await engine.initialize();
    console.log('✅ Engine initialized successfully\n');

    // Run tests
    await testBasicDetection(engine);
    await testDepressionMarkers(engine);
    await testNeuralValidation(engine);
    await testMarkerInfo(engine);
    await testSingleMessage(engine);
    await benchmarkDetection(engine);

    console.log('\n╔════════════════════════════════════════════════════════════╗');
    console.log('║              ✅ All tests completed!                       ║');
    console.log('╚════════════════════════════════════════════════════════════╝\n');
  } catch (error: any) {
    console.error('\n❌ Test failed:', error.message);
    console.error(error);
    process.exit(1);
  }
}

// Run tests
main();
