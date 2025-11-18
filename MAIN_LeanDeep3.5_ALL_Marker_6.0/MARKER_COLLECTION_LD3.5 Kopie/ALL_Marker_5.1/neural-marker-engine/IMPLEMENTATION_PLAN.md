# Implementation Plan: Neural Self-Learning Marker System

**Goal**: Migrate YAML markers to Supabase and build a self-learning neural network system for real-time pattern recognition and prediction.

---

## 📋 Overview

Transform the LeanDeep marker collection into a production-ready neural system that:
1. ✅ Stores 700+ markers in Supabase
2. 🧠 Uses neural networks to validate and predict patterns
3. 📊 Learns from conversation data automatically
4. 🔮 Predicts escalation, intervention moments, and future markers
5. 🔄 Improves accuracy through continuous learning

---

## Phase 1: Foundation & Migration (Week 1)

### Task 1.1: Environment Setup
**File**: `neural-marker-engine/.env`

**Steps**:
1. Create Supabase account at https://supabase.com
2. Create new project (choose region closest to users)
3. Copy credentials from Settings → API:
   - Project URL
   - Anon key (public)
   - Service role key (secret)
4. Create `.env` file:

```bash
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
MARKERS_BASE_PATH=../
```

**Verification**:
```bash
curl https://YOUR_PROJECT_URL/rest/v1/ \
  -H "apikey: YOUR_ANON_KEY"
# Should return: {"message":"Welcome to PostgREST"}
```

---

### Task 1.2: Install Dependencies
**Directory**: `neural-marker-engine/`

**Command**:
```bash
cd neural-marker-engine
npm install
```

**Expected packages**:
- `@supabase/supabase-js` - Database client
- `yaml` - YAML parser
- `dotenv` - Environment variables
- `typescript` - Type safety
- `tsx` - TypeScript execution

**Verification**:
```bash
npx tsx --version
# Should output version number
```

---

### Task 1.3: Database Schema Migration
**File**: `supabase/migrations/001_initial_schema.sql`

**Steps**:
1. Open Supabase Dashboard → SQL Editor
2. Create new query
3. Copy entire contents of `supabase/migrations/001_initial_schema.sql`
4. Execute query

**What this creates**:
- `markers` table - Stores all 700+ marker definitions
- `marker_events` table - Real-time detection stream
- `model_weights` table - Neural network parameters
- `cluster_centroids` table - Discovered patterns
- `conversation_sessions` table - Conversation metadata
- `detection_feedback` table - User corrections for learning

**Verification**:
```sql
-- Run in SQL Editor
SELECT
  tablename,
  (SELECT COUNT(*) FROM information_schema.columns
   WHERE table_name = tablename) as column_count
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

Expected output:
```
tablename                  | column_count
---------------------------+--------------
cluster_centroids          | 8
conversation_sessions      | 5
detection_feedback         | 7
marker_events              | 9
markers                    | 7
model_weights              | 7
```

---

### Task 1.4: Migrate YAML Markers to Supabase
**Script**: `src/scripts/migrate-markers.ts`

**Command**:
```bash
npm run migrate
```

**What happens**:
1. Scans directories:
   - `ATO_atomic/` - 329 markers
   - `SEM_semantic/` - 260 markers
   - `CLU_cluster/` - 91 markers
   - `MEMA_meta/` - 45 markers
2. Parses each YAML file
3. Validates marker dependencies
4. Uploads to Supabase `markers` table
5. Creates backup: `markers-backup.json`

**Expected output**:
```
Loading markers from: ../
Loaded 725 markers

Marker counts by category:
  ATOMIC:   329
  SEMANTIC: 260
  CLUSTER:  91
  META:     45

Migrating to Supabase...
✓ Migration complete!
  Success: 725
  Errors:  0

✓ Database contains 725 markers
```

**Verification**:
```bash
npm run migrate stats
```

Should show marker counts by category and language.

---

### Task 1.5: Test Basic Marker Loading
**Script**: `src/scripts/test-engine.ts`

**Command**:
```bash
npm test
```

**What this tests**:
1. Load markers from Supabase
2. Detect patterns in German conversation
3. Detect depression markers in English
4. Mock neural validation
5. Performance benchmark

**Expected output**:
```
✅ Engine initialized successfully

🧪 Test 1: Basic Marker Detection
Found X markers in conversation

🧪 Test 6: Performance Benchmark
  Average per conversation: ~30-50ms
  Throughput: ~20-40 conversations/second

✅ All tests completed!
```

---

## Phase 2: Neural Validator (Weeks 2-3)

### Task 2.1: Prepare Training Data
**File**: `src/scripts/prepare-training-data.ts` (NEW)

**Purpose**: Convert marker examples to training dataset

**Implementation**:
```typescript
import { loadAllMarkers } from '../utils/yaml-parser.js';

interface TrainingExample {
  text: string;
  markers: string[];
  label: 'positive' | 'negative';
}

async function prepareTrainingData() {
  const markers = loadAllMarkers('../');
  const trainingData: TrainingExample[] = [];

  for (const marker of markers) {
    // Positive examples
    if (marker.examples) {
      const examples = Array.isArray(marker.examples)
        ? marker.examples
        : marker.examples.positive || [];

      examples.forEach(text => {
        trainingData.push({
          text,
          markers: [marker.id],
          label: 'positive',
        });
      });

      // Negative examples
      if (!Array.isArray(marker.examples) && marker.examples.negative) {
        marker.examples.negative.forEach(text => {
          trainingData.push({
            text,
            markers: [],
            label: 'negative',
          });
        });
      }
    }
  }

  // Save to JSON
  fs.writeFileSync(
    'training-data.json',
    JSON.stringify(trainingData, null, 2)
  );

  console.log(`Generated ${trainingData.length} training examples`);
}
```

**Run**:
```bash
npx tsx src/scripts/prepare-training-data.ts
```

**Output**: `training-data.json` with ~5000+ examples

---

### Task 2.2: Train Neural Validator (Python)
**File**: `ml-models/train-validator.py` (NEW)

**Setup**:
```bash
mkdir ml-models
cd ml-models
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install transformers torch sentence-transformers onnx
```

**Training script**:
```python
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
import json

# Load training data
with open('../neural-marker-engine/training-data.json') as f:
    data = json.load(f)

# Prepare examples
train_examples = []
for item in data:
    # Create pairs: (text, marker_id) with similarity score
    label = 1.0 if item['label'] == 'positive' else 0.0
    for marker_id in item['markers']:
        train_examples.append(InputExample(
            texts=[item['text'], marker_id],
            label=label
        ))

# Load pre-trained model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Define loss
train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
train_loss = losses.CosineSimilarityLoss(model)

# Fine-tune
model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=3,
    warmup_steps=100,
    output_path='./marker-validator-model'
)

# Export to ONNX
model.save('./marker-validator-model', model_name='model')
print("✅ Model trained and saved!")
```

**Run**:
```bash
python ml-models/train-validator.py
```

**Output**: `ml-models/marker-validator-model/` directory

---

### Task 2.3: Convert Model to ONNX
**File**: `ml-models/export-onnx.py` (NEW)

```python
from sentence_transformers import SentenceTransformer
from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers import AutoTokenizer

# Load trained model
model = SentenceTransformer('./marker-validator-model')

# Export to ONNX
model.save('./marker-validator-onnx', model_name='model')

# Convert for edge deployment
ort_model = ORTModelForFeatureExtraction.from_pretrained(
    './marker-validator-model',
    export=True
)
tokenizer = AutoTokenizer.from_pretrained('./marker-validator-model')

ort_model.save_pretrained('./marker-validator-onnx')
tokenizer.save_pretrained('./marker-validator-onnx')

print("✅ ONNX model exported!")
```

**Run**:
```bash
python ml-models/export-onnx.py
```

**Output**: `marker-validator-onnx/model.onnx` (~22MB)

---

### Task 2.4: Deploy Edge Function
**File**: `supabase/functions/validate-markers/index.ts`

**Implementation**:
```typescript
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

// Load ONNX model (simplified - use actual ONNX runtime)
async function validateMarker(text: string, markerId: string): Promise<number> {
  // TODO: Implement actual ONNX inference
  // For now, simple heuristic
  const textLower = text.toLowerCase();
  const markerLower = markerId.toLowerCase();

  // Simple scoring based on text length and context
  let score = 0.5;
  if (textLower.length > 20) score += 0.1;
  if (textLower.split(/\s+/).length > 5) score += 0.1;

  return Math.min(score, 1.0);
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
      },
    });
  }

  try {
    const { context, candidates, options } = await req.json();
    const threshold = options?.threshold || 0.6;

    const validated = [];
    const rejected = [];

    for (const candidate of candidates) {
      // Get context text
      const contextText = context.map((m: any) => m.text).join(' ');

      // Validate with model
      const confidence = await validateMarker(contextText, candidate.marker_id);

      if (confidence >= threshold) {
        validated.push({
          ...candidate,
          validated: true,
          validation_confidence: confidence,
        });
      } else {
        rejected.push({
          ...candidate,
          validated: false,
          validation_confidence: confidence,
        });
      }
    }

    return new Response(
      JSON.stringify({ validated, rejected }),
      {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      }
    );
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );
  }
});
```

**Deploy**:
```bash
supabase functions deploy validate-markers
```

**Get URL**:
```bash
supabase functions list
# Copy URL: https://xxxxx.supabase.co/functions/v1/validate-markers
```

**Update `.env`**:
```bash
NEURAL_VALIDATOR_URL=https://xxxxx.supabase.co/functions/v1/validate-markers
```

---

## Phase 3: Self-Learning System (Weeks 4-6)

### Task 3.1: Pattern Discovery Engine
**File**: `src/engine/pattern-discovery.ts` (NEW)

**Purpose**: Automatically discover new marker patterns from conversations

**Implementation**:
```typescript
import { Message, Detection } from '../types/marker.types.js';

export class PatternDiscovery {
  /**
   * Extract n-grams from conversation
   */
  extractNGrams(messages: Message[], n: number = 3): Map<string, number> {
    const ngrams = new Map<string, number>();

    for (const msg of messages) {
      const words = msg.text.toLowerCase().split(/\s+/);

      for (let i = 0; i <= words.length - n; i++) {
        const ngram = words.slice(i, i + n).join(' ');
        ngrams.set(ngram, (ngrams.get(ngram) || 0) + 1);
      }
    }

    return ngrams;
  }

  /**
   * Find frequent patterns not covered by existing markers
   */
  async discoverNewPatterns(
    conversations: Message[][],
    existingMarkers: Set<string>,
    minFrequency: number = 5
  ): Promise<Array<{ pattern: string; frequency: number; contexts: string[] }>> {
    const allNGrams = new Map<string, { count: number; contexts: string[] }>();

    // Collect n-grams across all conversations
    for (const conv of conversations) {
      const ngrams = this.extractNGrams(conv, 3);

      ngrams.forEach((count, pattern) => {
        if (!allNGrams.has(pattern)) {
          allNGrams.set(pattern, { count: 0, contexts: [] });
        }
        const data = allNGrams.get(pattern)!;
        data.count += count;
        data.contexts.push(conv.map(m => m.text).join(' | '));
      });
    }

    // Filter frequent patterns
    const candidates = Array.from(allNGrams.entries())
      .filter(([pattern, data]) => data.count >= minFrequency)
      .filter(([pattern]) => !this.matchesExistingMarker(pattern, existingMarkers))
      .map(([pattern, data]) => ({
        pattern,
        frequency: data.count,
        contexts: data.contexts.slice(0, 5), // Keep 5 examples
      }))
      .sort((a, b) => b.frequency - a.frequency);

    return candidates;
  }

  /**
   * Check if pattern matches existing markers
   */
  private matchesExistingMarker(pattern: string, markers: Set<string>): boolean {
    // Simple check - in production, use embedding similarity
    const words = pattern.split(/\s+/);
    return words.some(word => {
      return Array.from(markers).some(marker =>
        marker.toLowerCase().includes(word)
      );
    });
  }

  /**
   * Cluster similar patterns
   */
  async clusterPatterns(
    patterns: Array<{ pattern: string; frequency: number }>,
    similarityThreshold: number = 0.7
  ): Promise<Array<{ centroid: string; members: string[] }>> {
    // Simple clustering based on word overlap
    const clusters: Array<{ centroid: string; members: string[] }> = [];

    for (const { pattern } of patterns) {
      let assigned = false;

      // Try to assign to existing cluster
      for (const cluster of clusters) {
        if (this.similarity(pattern, cluster.centroid) >= similarityThreshold) {
          cluster.members.push(pattern);
          assigned = true;
          break;
        }
      }

      // Create new cluster
      if (!assigned) {
        clusters.push({
          centroid: pattern,
          members: [pattern],
        });
      }
    }

    return clusters;
  }

  /**
   * Simple word overlap similarity
   */
  private similarity(text1: string, text2: string): number {
    const words1 = new Set(text1.toLowerCase().split(/\s+/));
    const words2 = new Set(text2.toLowerCase().split(/\s+/));

    const intersection = new Set([...words1].filter(w => words2.has(w)));
    const union = new Set([...words1, ...words2]);

    return intersection.size / union.size;
  }
}
```

---

### Task 3.2: Continuous Learning Pipeline
**File**: `src/scripts/learn-from-conversations.ts` (NEW)

```typescript
import { createClient } from '@supabase/supabase-js';
import { PatternDiscovery } from '../engine/pattern-discovery.js';
import { MarkerEngine } from '../engine/marker-engine.js';

async function runLearningPipeline() {
  const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );

  const engine = new MarkerEngine({
    supabase_url: process.env.SUPABASE_URL!,
    supabase_key: process.env.SUPABASE_SERVICE_ROLE_KEY!,
  });

  await engine.initialize();

  // 1. Load recent conversations (last 7 days)
  const { data: sessions } = await supabase
    .from('conversation_sessions')
    .select('*, marker_events(*)')
    .gte('started_at', new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString());

  console.log(`Loaded ${sessions?.length || 0} conversation sessions`);

  // 2. Extract conversation messages (simulated - you'd load actual messages)
  const conversations = sessions?.map(s => {
    // Extract messages from session
    return []; // Placeholder
  }) || [];

  // 3. Discover new patterns
  const discovery = new PatternDiscovery();
  const existingMarkers = new Set(
    engine.getMarkersByCategory('ATOMIC').map(m => m.id)
  );

  const newPatterns = await discovery.discoverNewPatterns(
    conversations,
    existingMarkers,
    5 // min frequency
  );

  console.log(`\nDiscovered ${newPatterns.length} new patterns:`);
  newPatterns.slice(0, 10).forEach(p => {
    console.log(`  "${p.pattern}" (frequency: ${p.frequency})`);
  });

  // 4. Cluster patterns
  const clusters = await discovery.clusterPatterns(newPatterns, 0.7);
  console.log(`\nClustered into ${clusters.length} groups`);

  // 5. Save to database for review
  for (const cluster of clusters.slice(0, 10)) {
    await supabase.from('cluster_centroids').insert({
      cluster_type: 'ato_candidate',
      description: cluster.centroid,
      frequency: cluster.members.length,
      examples: cluster.members,
      confidence: 0.5,
    });
  }

  console.log('\n✅ Learning pipeline complete!');
}

runLearningPipeline();
```

**Schedule** (run weekly):
```bash
# Add to cron or use Supabase cron extension
0 0 * * 0 cd /path/to/neural-marker-engine && npx tsx src/scripts/learn-from-conversations.ts
```

---

## Phase 4: Prediction Engine (Weeks 7-9)

### Task 4.1: Escalation Predictor
**File**: `src/engine/escalation-predictor.ts` (NEW)

```typescript
import { Message, Detection } from '../types/marker.types.js';

export class EscalationPredictor {
  /**
   * Predict probability of conversation escalating
   */
  predict(messages: Message[], detections: Detection[]): number {
    // Feature extraction
    const features = this.extractFeatures(messages, detections);

    // Simple rule-based prediction (replace with ML model)
    let escalationScore = 0.0;

    // Feature 1: Negative marker trend
    const negativeMarkers = ['ATO_ANGER', 'ATO_BLAME_SHIFT', 'ATO_CRITICISM'];
    const negativeCount = detections.filter(d =>
      negativeMarkers.some(nm => d.marker_id.includes(nm))
    ).length;
    escalationScore += Math.min(negativeCount * 0.1, 0.4);

    // Feature 2: Increasing message frequency
    if (messages.length >= 2) {
      const recentGap = messages[messages.length - 1].timestamp -
                        messages[messages.length - 2].timestamp;
      if (recentGap < 2000) { // < 2 seconds
        escalationScore += 0.2;
      }
    }

    // Feature 3: Absolutist language
    const absolutistCount = detections.filter(d =>
      d.marker_id === 'ATO_ABSOLUTIZER'
    ).length;
    escalationScore += Math.min(absolutistCount * 0.05, 0.2);

    // Feature 4: Cluster markers present
    const clusterMarkers = detections.filter(d => d.category === 'CLUSTER');
    escalationScore += Math.min(clusterMarkers.length * 0.1, 0.3);

    return Math.min(escalationScore, 1.0);
  }

  private extractFeatures(messages: Message[], detections: Detection[]) {
    return {
      messageCount: messages.length,
      avgMessageLength: messages.reduce((sum, m) => sum + m.text.length, 0) / messages.length,
      detectionCount: detections.length,
      uniqueMarkers: new Set(detections.map(d => d.marker_id)).size,
      clusterCount: detections.filter(d => d.category === 'CLUSTER').length,
    };
  }
}
```

---

### Task 4.2: Intervention Recommender
**File**: `src/engine/intervention-recommender.ts` (NEW)

```typescript
export class InterventionRecommender {
  recommend(escalationScore: number, detections: Detection[]): {
    shouldIntervene: boolean;
    suggestion: string;
    priority: 'low' | 'medium' | 'high';
  } {
    // High escalation - urgent intervention
    if (escalationScore > 0.7) {
      return {
        shouldIntervene: true,
        suggestion: 'Consider taking a break. This conversation is escalating quickly.',
        priority: 'high',
      };
    }

    // Medium escalation - preventive suggestion
    if (escalationScore > 0.4) {
      const hasAbsolutist = detections.some(d => d.marker_id === 'ATO_ABSOLUTIZER');
      if (hasAbsolutist) {
        return {
          shouldIntervene: true,
          suggestion: 'Try using "sometimes" instead of "always/never" to reduce tension.',
          priority: 'medium',
        };
      }
    }

    // Check for specific patterns
    const hasApology = detections.some(d => d.marker_id === 'ATO_APOLOGY');
    if (hasApology && escalationScore > 0.3) {
      return {
        shouldIntervene: true,
        suggestion: 'An apology was offered - this might be a good moment to acknowledge it.',
        priority: 'medium',
      };
    }

    return {
      shouldIntervene: false,
      suggestion: '',
      priority: 'low',
    };
  }
}
```

---

## Phase 5: Production Deployment (Week 10)

### Task 5.1: Performance Optimization

**Caching Strategy**:
```typescript
// src/engine/marker-cache.ts
export class MarkerCache {
  private cache = new Map<string, { data: any; expiry: number }>();

  set(key: string, data: any, ttlSeconds: number = 3600) {
    this.cache.set(key, {
      data,
      expiry: Date.now() + ttlSeconds * 1000,
    });
  }

  get(key: string): any | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    if (Date.now() > entry.expiry) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }
}
```

---

### Task 5.2: Monitoring & Analytics

**Create dashboard query**:
```sql
-- supabase/queries/marker-analytics.sql
CREATE OR REPLACE VIEW marker_analytics AS
SELECT
  marker_id,
  COUNT(*) as detection_count,
  AVG(confidence) as avg_confidence,
  COUNT(CASE WHEN validated = true THEN 1 END) as validated_count,
  COUNT(CASE WHEN validated = false THEN 1 END) as rejected_count
FROM marker_events
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY marker_id
ORDER BY detection_count DESC;
```

---

## 🎯 Success Criteria

### Week 1 Checkpoints:
- [ ] Supabase project created
- [ ] 725 markers migrated successfully
- [ ] Test suite passes (all 6 tests green)
- [ ] Can detect markers in sample conversation

### Week 3 Checkpoints:
- [ ] Neural validator deployed to edge function
- [ ] Training data prepared (5000+ examples)
- [ ] Model achieves >80% validation accuracy
- [ ] False positive rate < 20%

### Week 6 Checkpoints:
- [ ] Pattern discovery finds 10+ new candidates
- [ ] Continuous learning pipeline running weekly
- [ ] New patterns saved to cluster_centroids table

### Week 9 Checkpoints:
- [ ] Escalation prediction >70% accuracy
- [ ] Intervention suggestions contextually appropriate
- [ ] System responds in <2 seconds end-to-end

### Week 10 (Production):
- [ ] Cache hit rate >80%
- [ ] Database queries <100ms P95
- [ ] Edge function uptime >99.9%
- [ ] Zero data breaches/privacy violations

---

## 📞 Support & Next Steps

After completing Phase 1, you'll have:
- ✅ 725 markers in Supabase
- ✅ Working detection engine
- ✅ Foundation for neural models

After Phase 5, you'll have:
- 🧠 Self-learning neural system
- 🔮 Real-time prediction
- 📊 Continuous improvement
- 🚀 Production-ready platform

**Ready to start?** Begin with Task 1.1!
