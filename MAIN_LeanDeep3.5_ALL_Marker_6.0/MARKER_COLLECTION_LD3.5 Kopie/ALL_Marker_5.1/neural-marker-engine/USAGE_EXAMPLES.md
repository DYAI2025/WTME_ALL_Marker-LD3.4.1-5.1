# Usage Examples

This document provides practical examples for using the Neural Marker Engine.

## Table of Contents

1. [Basic Setup](#basic-setup)
2. [Simple Detection](#simple-detection)
3. [Real-Time Conversation Analysis](#real-time-conversation-analysis)
4. [Neural Validation](#neural-validation)
5. [Supabase Integration](#supabase-integration)
6. [Advanced Use Cases](#advanced-use-cases)

---

## Basic Setup

### Installation

```bash
npm install
npm run build
```

### Environment Configuration

```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

---

## Simple Detection

### Example 1: Detect Absolutist Language

```typescript
import { createNeuralMarkerEngine } from './src/index.js';

const engine = await createNeuralMarkerEngine(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

const message = {
  id: '1',
  speaker: 'User',
  text: 'Du kommst immer zu spät! Das funktioniert nie!',
  timestamp: Date.now(),
};

const detections = engine.detectInMessage(message);

console.log('Detected markers:', detections.map(d => d.marker_id));
// Output: ['ATO_ABSOLUTIZER', 'ATO_ABSOLUTIZER']
```

### Example 2: Analyze Single Message

```typescript
import { MarkerEngine } from './src/engine/marker-engine.js';

const engine = new MarkerEngine({
  supabase_url: process.env.SUPABASE_URL!,
  supabase_key: process.env.SUPABASE_ANON_KEY!,
  enable_caching: true,
  cache_ttl_seconds: 3600,
});

await engine.initialize();

const message = {
  id: 'msg1',
  speaker: 'Alice',
  text: 'Tut mir leid, ich wollte dich nicht verletzen.',
  timestamp: Date.now(),
};

const detections = engine.detectInMessage(message);

detections.forEach(d => {
  console.log(`Marker: ${d.marker_id}`);
  console.log(`Confidence: ${d.confidence}`);
  console.log(`Matched: "${d.matched_text}"`);
});
```

---

## Real-Time Conversation Analysis

### Example 3: Streaming Conversation

```typescript
import { createNeuralMarkerEngine, Message } from './src/index.js';

const engine = await createNeuralMarkerEngine(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

// Simulated conversation stream
const conversationHistory: Message[] = [];

function addMessage(speaker: string, text: string) {
  const message: Message = {
    id: `msg-${Date.now()}`,
    speaker,
    text,
    timestamp: Date.now(),
  };

  conversationHistory.push(message);

  // Analyze conversation context
  detectPatterns();
}

async function detectPatterns() {
  // Keep last 20 messages for context
  const recentMessages = conversationHistory.slice(-20);

  const detections = await engine.detectInConversation(recentMessages);

  // Group by category
  const clusterMarkers = detections.filter(d => d.category === 'CLUSTER');
  const metaMarkers = detections.filter(d => d.category === 'META');

  if (clusterMarkers.length > 0) {
    console.log('🔔 Cluster patterns detected:');
    clusterMarkers.forEach(d => {
      console.log(`  - ${d.marker_id} (confidence: ${d.confidence.toFixed(2)})`);
    });
  }

  if (metaMarkers.length > 0) {
    console.log('⚠️  Meta patterns detected:');
    metaMarkers.forEach(d => {
      console.log(`  - ${d.marker_id} (confidence: ${d.confidence.toFixed(2)})`);
    });
  }
}

// Simulate conversation
addMessage('Alice', 'Du kommst immer zu spät!');
addMessage('Bob', 'Das stimmt nicht. Ich versuche mein Bestes.');
addMessage('Alice', 'Nie hörst du mir zu.');
addMessage('Bob', 'Ich höre dir zu, aber du greifst mich ständig an.');
```

### Example 4: Depression Detection

```typescript
import { createNeuralMarkerEngine, Message } from './src/index.js';

const engine = await createNeuralMarkerEngine(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

const therapeuticConversation: Message[] = [
  {
    id: 'msg1',
    speaker: 'Client',
    text: 'I feel so sad and hopeless every day.',
    timestamp: Date.now() - 10000,
  },
  {
    id: 'msg2',
    speaker: 'Client',
    text: 'The pain in my chest won\'t go away.',
    timestamp: Date.now() - 8000,
  },
  {
    id: 'msg3',
    speaker: 'Client',
    text: 'I blame myself for everything. My life was better before.',
    timestamp: Date.now() - 6000,
  },
];

const detections = await engine.detectInConversation(therapeuticConversation);

// Filter for depression-related markers
const depressionMarkers = detections.filter(d =>
  d.marker_id.includes('DEPRESSION') || d.marker_id.includes('DEPRESSIVE')
);

console.log(`Found ${depressionMarkers.length} depression-related markers:`);
depressionMarkers.forEach(d => {
  console.log(`  ${d.marker_id}: ${d.confidence.toFixed(2)}`);
});

// Check for meta-level depressive profile
const depressionProfile = detections.find(
  d => d.marker_id === 'MEMA_DEPRESSIVE_LANGUAGE_PROFILE'
);

if (depressionProfile) {
  console.log('\n⚠️  WARNING: Depressive language profile detected');
  console.log(`Confidence: ${depressionProfile.confidence.toFixed(2)}`);
  console.log('Components:', depressionProfile.matched_patterns);
}
```

---

## Neural Validation

### Example 5: Mock Neural Validation

```typescript
import { MarkerEngine } from './src/engine/marker-engine.js';
import { MockNeuralValidator } from './src/engine/neural-validator.js';

// Initialize engine
const engine = new MarkerEngine({
  supabase_url: process.env.SUPABASE_URL!,
  supabase_key: process.env.SUPABASE_ANON_KEY!,
});

await engine.initialize();

// Create mock validator (simulates neural network)
const validator = new MockNeuralValidator(0.6); // 60% confidence threshold

const conversation = [
  {
    id: 'msg1',
    speaker: 'A',
    text: 'Immer das gleiche mit dir!',
    timestamp: Date.now(),
  },
];

// Get initial detections
const detections = await engine.detectInConversation(conversation);
console.log(`Initial detections: ${detections.length}`);

// Validate with neural model
const validated = await validator.validate(conversation, detections);

console.log('\nValidation Results:');
console.log(`Accepted: ${validated.validated.length}`);
console.log(`Rejected: ${validated.rejected?.length || 0}`);

validated.validated.forEach(d => {
  console.log(`✅ ${d.marker_id}`);
  console.log(`   Rule confidence: ${d.confidence.toFixed(2)}`);
  console.log(`   Neural confidence: ${d.validation_confidence?.toFixed(2)}`);
});
```

### Example 6: Production Neural Validation

```typescript
import { MarkerEngine } from './src/engine/marker-engine.js';
import { NeuralValidator } from './src/engine/neural-validator.js';

const engine = new MarkerEngine({
  supabase_url: process.env.SUPABASE_URL!,
  supabase_key: process.env.SUPABASE_ANON_KEY!,
});

await engine.initialize();

// Connect to real neural validator (Supabase Edge Function)
const validator = new NeuralValidator(
  process.env.NEURAL_VALIDATOR_URL!,
  0.6, // threshold
  true // enabled
);

// Check if validator is available
const isHealthy = await validator.healthCheck();
console.log(`Neural validator status: ${isHealthy ? '✅ Online' : '❌ Offline'}`);

if (isHealthy) {
  const conversation = [/* your messages */];
  const detections = await engine.detectInConversation(conversation);
  const validated = await validator.validate(conversation, detections);

  console.log('Validated detections:', validated.validated);
}
```

---

## Supabase Integration

### Example 7: Save Detections to Database

```typescript
import { createClient } from '@supabase/supabase-js';
import { createNeuralMarkerEngine } from './src/index.js';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

const engine = await createNeuralMarkerEngine(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

// Create a conversation session
const { data: session } = await supabase
  .from('conversation_sessions')
  .insert({
    user_id: 'user-123',
    metadata: { context: 'therapy' },
  })
  .select()
  .single();

const sessionId = session.id;

// Detect markers
const conversation = [/* your messages */];
const detections = await engine.detectInConversation(conversation);

// Save to database
for (const detection of detections) {
  await supabase.from('marker_events').insert({
    session_id: sessionId,
    marker_id: detection.marker_id,
    confidence: detection.confidence,
    validated: detection.validated,
    validation_confidence: detection.validation_confidence,
    metadata: {
      matched_text: detection.matched_text,
      position: detection.position,
    },
  });
}

console.log(`Saved ${detections.length} detections to database`);
```

### Example 8: Real-Time Marker Stream

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

// Subscribe to real-time marker events
const channel = supabase
  .channel('marker-stream')
  .on(
    'postgres_changes',
    {
      event: 'INSERT',
      schema: 'public',
      table: 'marker_events',
    },
    (payload) => {
      console.log('New marker detected:', payload.new);

      // Handle specific markers
      if (payload.new.marker_id.includes('DEPRESSION')) {
        console.log('⚠️  Depression marker detected!');
        // Trigger intervention, notification, etc.
      }
    }
  )
  .subscribe();
```

---

## Advanced Use Cases

### Example 9: Custom Marker Filtering

```typescript
import { createNeuralMarkerEngine } from './src/index.js';

const engine = await createNeuralMarkerEngine(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

const conversation = [/* your messages */];
const allDetections = await engine.detectInConversation(conversation);

// Filter for high-confidence CLUSTER markers only
const highConfidenceClusters = allDetections.filter(
  d => d.category === 'CLUSTER' && d.confidence > 0.7
);

// Group by marker type
const groupedByType = highConfidenceClusters.reduce((acc, d) => {
  const prefix = d.marker_id.split('_')[1]; // e.g., "DEPRESSIVE"
  if (!acc[prefix]) acc[prefix] = [];
  acc[prefix].push(d);
  return acc;
}, {} as Record<string, any[]>);

console.log('High-confidence cluster patterns:');
Object.entries(groupedByType).forEach(([type, markers]) => {
  console.log(`\n${type}:`);
  markers.forEach(m => console.log(`  - ${m.marker_id}`));
});
```

### Example 10: Performance Monitoring

```typescript
import { createNeuralMarkerEngine, Message } from './src/index.js';

const engine = await createNeuralMarkerEngine(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

async function analyzeWithTiming(messages: Message[]) {
  const start = Date.now();

  const detections = await engine.detectInConversation(messages);

  const elapsed = Date.now() - start;

  console.log('\n📊 Performance Metrics:');
  console.log(`  Messages analyzed: ${messages.length}`);
  console.log(`  Detections found: ${detections.length}`);
  console.log(`  Time elapsed: ${elapsed}ms`);
  console.log(`  Avg per message: ${(elapsed / messages.length).toFixed(2)}ms`);

  return detections;
}

// Test with different conversation sizes
const shortConvo = [/* 5 messages */];
const mediumConvo = [/* 20 messages */];
const longConvo = [/* 50 messages */];

await analyzeWithTiming(shortConvo);
await analyzeWithTiming(mediumConvo);
await analyzeWithTiming(longConvo);
```

### Example 11: Batch Processing Conversations

```typescript
import { createNeuralMarkerEngine, Message } from './src/index.js';

const engine = await createNeuralMarkerEngine(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

// Load multiple conversations from database or file
const conversations: Message[][] = [
  [/* conversation 1 */],
  [/* conversation 2 */],
  [/* conversation 3 */],
];

const results = await Promise.all(
  conversations.map(async (conv, idx) => {
    const detections = await engine.detectInConversation(conv);

    return {
      conversationId: idx,
      messageCount: conv.length,
      detectionCount: detections.length,
      categories: {
        atomic: detections.filter(d => d.category === 'ATOMIC').length,
        semantic: detections.filter(d => d.category === 'SEMANTIC').length,
        cluster: detections.filter(d => d.category === 'CLUSTER').length,
        meta: detections.filter(d => d.category === 'META').length,
      },
    };
  })
);

console.log('Batch Analysis Results:');
console.table(results);
```

### Example 12: Marker Dependency Graph

```typescript
import { createNeuralMarkerEngine } from './src/index.js';

const engine = await createNeuralMarkerEngine(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

// Build dependency graph for MEMA marker
const metaMarker = engine.getMarker('MEMA_DEPRESSIVE_LANGUAGE_PROFILE');

if (metaMarker && metaMarker.category === 'META') {
  console.log(`\nDependency tree for ${metaMarker.id}:`);
  console.log('└─ META');

  metaMarker.components.forEach(compId => {
    const comp = engine.getMarker(compId);
    if (comp) {
      console.log(`   ├─ ${comp.id} (${comp.category})`);

      if (comp.category === 'CLUSTER') {
        const cluster = comp as any;
        const subComponents = cluster.components || [];
        subComponents.forEach((subId: string) => {
          console.log(`   │  └─ ${subId}`);
        });
      }
    }
  });
}
```

---

## Running Examples

To run these examples:

1. Install dependencies: `npm install`
2. Configure `.env` with your Supabase credentials
3. Migrate markers: `npm run migrate`
4. Run test suite: `npm test`

Or create a custom script:

```typescript
// examples/my-example.ts
import { createNeuralMarkerEngine } from '../src/index.js';

// Your code here...

// Run with:
// npx tsx examples/my-example.ts
```

---

## Need Help?

- Check the [README.md](./README.md) for setup instructions
- Review the [type definitions](./src/types/marker.types.ts) for API reference
- Run the test suite for working examples: `npm test`
