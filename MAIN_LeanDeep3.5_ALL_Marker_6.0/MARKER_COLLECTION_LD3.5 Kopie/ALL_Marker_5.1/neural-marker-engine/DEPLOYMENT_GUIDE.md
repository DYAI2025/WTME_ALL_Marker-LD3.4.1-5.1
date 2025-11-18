# Deployment Guide

This guide walks you through deploying the Neural Marker Engine to production with Supabase and edge functions.

## 🎯 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT APPLICATION                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Neural Marker Engine (Browser/Node.js)            │    │
│  │  • Rule-based detection (local)                    │    │
│  │  • Marker cache (IndexedDB/Memory)                 │    │
│  │  • Federated learning (optional)                   │    │
│  └────────────┬───────────────────────────────────────┘    │
└───────────────┼──────────────────────────────────────────────┘
                │
                │ HTTPS/WebSocket
                │
┌───────────────▼──────────────────────────────────────────────┐
│                     SUPABASE CLOUD                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │  PostgreSQL Database                                │    │
│  │  • markers table (700+ definitions)                 │    │
│  │  • marker_events (realtime stream)                  │    │
│  │  • cluster_centroids (discoveries)                  │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Edge Functions (Deno)                              │    │
│  │  • validate-markers (neural validator)              │    │
│  │  • predict-patterns (escalation, intervention)      │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Realtime                                           │    │
│  │  • WebSocket subscriptions                          │    │
│  │  • Live marker event streams                        │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

- Node.js 18+
- npm or yarn
- Supabase account (free tier works)
- Supabase CLI: `npm install -g supabase`

---

## Step 1: Set Up Supabase Project

### 1.1 Create Project

1. Go to [supabase.com](https://supabase.com)
2. Click "New Project"
3. Choose organization and region
4. Set strong database password
5. Wait for project provisioning (~2 minutes)

### 1.2 Get Credentials

From your project dashboard:

1. Go to **Settings** → **API**
2. Copy:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **Anon/Public Key** (for client apps)
   - **Service Role Key** (for migration, keep secret!)

### 1.3 Configure Local Environment

```bash
cd neural-marker-engine
cp .env.example .env
```

Edit `.env`:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
MARKERS_BASE_PATH=../
```

---

## Step 2: Database Setup

### 2.1 Run Migrations

Option A: Using Supabase Dashboard

1. Go to **SQL Editor** in dashboard
2. Create new query
3. Paste contents of `supabase/migrations/001_initial_schema.sql`
4. Click "Run"

Option B: Using Supabase CLI

```bash
supabase link --project-ref your-project-ref
supabase db push
```

### 2.2 Verify Schema

```sql
-- Run in SQL Editor
SELECT tablename FROM pg_tables WHERE schemaname = 'public';
```

Should see:
- markers
- marker_events
- model_weights
- cluster_centroids
- conversation_sessions
- detection_feedback

---

## Step 3: Migrate Markers

### 3.1 Install Dependencies

```bash
npm install
```

### 3.2 Run Migration Script

```bash
npm run migrate
```

This will:
1. Parse all YAML markers (ATO, SEM, CLU, MEMA)
2. Validate dependencies
3. Upload to `markers` table
4. Create backup JSON file

### 3.3 Verify Migration

```bash
npm run migrate stats
```

Expected output:
```
Total markers: 725

By category:
  ATOMIC    : 329
  SEMANTIC  : 260
  CLUSTER   : 91
  META      : 45
```

---

## Step 4: Deploy Edge Functions (Optional)

Edge functions enable neural validation. Skip if using rule-based only.

### 4.1 Install Supabase CLI

```bash
npm install -g supabase
supabase login
```

### 4.2 Initialize Functions

```bash
supabase functions new validate-markers
```

### 4.3 Implement Validator

Create `supabase/functions/validate-markers/index.ts`:

```typescript
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';

serve(async (req) => {
  // CORS headers
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

    // Simple mock validation (replace with actual model)
    const validated = candidates.map((c: any) => ({
      ...c,
      validated: true,
      validation_confidence: 0.8,
    }));

    return new Response(
      JSON.stringify({ validated }),
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
      {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
});
```

### 4.4 Deploy Function

```bash
supabase functions deploy validate-markers
```

### 4.5 Get Function URL

```bash
supabase functions list
```

Copy the URL (e.g., `https://xxx.supabase.co/functions/v1/validate-markers`)

Update `.env`:
```env
NEURAL_VALIDATOR_URL=https://xxx.supabase.co/functions/v1/validate-markers
```

---

## Step 5: Client Integration

### 5.1 Install Package

```bash
npm install /path/to/neural-marker-engine
```

Or add to `package.json`:
```json
{
  "dependencies": {
    "neural-marker-engine": "file:../neural-marker-engine"
  }
}
```

### 5.2 Initialize Engine

```typescript
import { createNeuralMarkerEngine } from 'neural-marker-engine';

const engine = await createNeuralMarkerEngine(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  process.env.NEXT_PUBLIC_NEURAL_VALIDATOR_URL
);

// Use engine
const detections = await engine.detectInConversation(messages);
```

### 5.3 Browser Bundle (Optional)

For browser use with bundlers (Vite, Webpack):

```typescript
// vite.config.ts
export default {
  optimizeDeps: {
    include: ['neural-marker-engine'],
  },
};
```

---

## Step 6: Enable Realtime (Optional)

### 6.1 Enable Realtime on Table

In Supabase Dashboard:
1. Go to **Database** → **Replication**
2. Enable `marker_events` table
3. Save

### 6.2 Subscribe to Events

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

const channel = supabase
  .channel('markers')
  .on(
    'postgres_changes',
    {
      event: 'INSERT',
      schema: 'public',
      table: 'marker_events',
    },
    (payload) => {
      console.log('New marker:', payload.new);
    }
  )
  .subscribe();
```

---

## Step 7: Production Checklist

### Security

- [ ] Enable Row Level Security (RLS) on all tables
- [ ] Never expose `SUPABASE_SERVICE_ROLE_KEY` in client code
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS only in production
- [ ] Set up CORS policies for Edge Functions

### Performance

- [ ] Enable marker caching (`enable_caching: true`)
- [ ] Set appropriate `cache_ttl_seconds` (3600 = 1 hour)
- [ ] Use batch validation for multiple detections
- [ ] Consider CDN for static assets
- [ ] Monitor database query performance

### Monitoring

- [ ] Set up Supabase logs monitoring
- [ ] Track Edge Function errors
- [ ] Monitor database size and usage
- [ ] Set up alerts for high-confidence detections
- [ ] Log validation performance metrics

### Backup

- [ ] Enable Supabase automatic backups
- [ ] Keep local backup: `npm run migrate` creates `markers-backup.json`
- [ ] Version control your marker YAML files
- [ ] Document custom markers and changes

---

## Step 8: Scaling Considerations

### Database Scaling

**Free Tier**: 500MB, suitable for development
**Pro Tier**: 8GB+, recommended for production

Monitor:
- `markers` table size (~1-5MB for 700 markers)
- `marker_events` growth (archive old events)
- Connection pool usage

### Edge Function Scaling

Supabase Edge Functions auto-scale, but monitor:
- Invocation count (free: 500K/month)
- Execution time (optimize for < 2 seconds)
- Cold start latency

### Client-Side Optimization

```typescript
// Lazy load engine
const lazyEngine = async () => {
  const { createNeuralMarkerEngine } = await import('neural-marker-engine');
  return createNeuralMarkerEngine(url, key);
};

// Use service worker for caching
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}
```

---

## Troubleshooting

### Migration Fails

**Error**: "Failed to load markers"

**Solution**:
1. Check `MARKERS_BASE_PATH` in `.env`
2. Verify YAML files are valid: `npm run migrate`
3. Check database permissions

### Neural Validation Not Working

**Error**: "Validation failed: 404"

**Solution**:
1. Verify Edge Function is deployed: `supabase functions list`
2. Check `NEURAL_VALIDATOR_URL` in `.env`
3. Test function directly: `curl https://your-function-url/health`

### Performance Issues

**Symptom**: Slow detection (> 1 second per message)

**Solutions**:
1. Enable caching: `enable_caching: true`
2. Reduce batch size if too large
3. Profile with: `console.time('detection')`
4. Consider worker threads for heavy processing

### Database Connection Errors

**Error**: "Connection refused"

**Solution**:
1. Check Supabase project is active
2. Verify URL and keys in `.env`
3. Check network/firewall settings
4. Test with: `curl https://your-project.supabase.co/rest/v1/`

---

## Next Steps

- [ ] Implement actual neural model in Edge Function
- [ ] Set up federated learning pipeline
- [ ] Add prediction engine (escalation, intervention)
- [ ] Create dashboard for marker analytics
- [ ] Implement A/B testing for marker effectiveness

---

## Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Edge Functions Guide](https://supabase.com/docs/guides/functions)
- [PostgreSQL + pgvector](https://github.com/pgvector/pgvector)
- [Deno Deploy](https://deno.com/deploy)

---

**Need help?** Open an issue on GitHub or contact support.
