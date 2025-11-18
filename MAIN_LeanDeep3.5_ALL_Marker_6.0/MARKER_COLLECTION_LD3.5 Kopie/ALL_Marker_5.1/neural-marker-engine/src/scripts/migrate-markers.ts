#!/usr/bin/env tsx
import { createClient } from '@supabase/supabase-js';
import * as dotenv from 'dotenv';
import * as path from 'path';
import { loadAllMarkers, validateMarkerDependencies, groupMarkersByCategory, exportMarkersToJson } from '../utils/yaml-parser.js';
import { Marker } from '../types/marker.types.js';

dotenv.config();

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const MARKERS_BASE_PATH = process.env.MARKERS_BASE_PATH || '../';

if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

/**
 * Migrate markers from YAML to Supabase
 */
async function migrateMarkers() {
  console.log('Starting marker migration...\n');

  // Step 1: Load all markers from YAML
  console.log(`Loading markers from: ${MARKERS_BASE_PATH}`);
  const markers = loadAllMarkers(MARKERS_BASE_PATH);
  console.log(`Loaded ${markers.length} markers\n`);

  // Step 2: Validate dependencies
  console.log('Validating marker dependencies...');
  const missingDeps = validateMarkerDependencies(markers);
  if (missingDeps.length > 0) {
    console.warn(`⚠️  Warning: Found ${missingDeps.length} missing dependencies:`);
    console.warn(missingDeps.slice(0, 10).join(', '));
    if (missingDeps.length > 10) {
      console.warn(`... and ${missingDeps.length - 10} more`);
    }
    console.log('');
  } else {
    console.log('✓ All dependencies validated\n');
  }

  // Step 3: Group by category
  const grouped = groupMarkersByCategory(markers);
  console.log('Marker counts by category:');
  console.log(`  ATOMIC:   ${grouped.ATOMIC.length}`);
  console.log(`  SEMANTIC: ${grouped.SEMANTIC.length}`);
  console.log(`  CLUSTER:  ${grouped.CLUSTER.length}`);
  console.log(`  META:     ${grouped.META.length}\n`);

  // Step 4: Export to JSON (backup)
  const jsonBackupPath = path.join(process.cwd(), 'markers-backup.json');
  exportMarkersToJson(markers, jsonBackupPath);

  // Step 5: Migrate to Supabase
  console.log('Migrating to Supabase...');

  let successCount = 0;
  let errorCount = 0;
  const errors: Array<{ id: string; error: string }> = [];

  for (const marker of markers) {
    try {
      const { error } = await supabase.from('markers').upsert({
        id: marker.id,
        category: marker.category,
        version: marker.version || '3.4',
        lang: marker.lang,
        definition: marker,
        updated_at: new Date().toISOString(),
      }, {
        onConflict: 'id', // Update if exists
      });

      if (error) {
        throw error;
      }

      successCount++;
      if (successCount % 50 === 0) {
        process.stdout.write(`  Migrated ${successCount}/${markers.length}...\r`);
      }
    } catch (error: any) {
      errorCount++;
      errors.push({
        id: marker.id,
        error: error.message || String(error),
      });
    }
  }

  console.log(`\n✓ Migration complete!`);
  console.log(`  Success: ${successCount}`);
  console.log(`  Errors:  ${errorCount}\n`);

  if (errors.length > 0) {
    console.log('Errors encountered:');
    errors.slice(0, 5).forEach(({ id, error }) => {
      console.log(`  ${id}: ${error}`);
    });
    if (errors.length > 5) {
      console.log(`  ... and ${errors.length - 5} more errors`);
    }
  }

  // Step 6: Verify migration
  console.log('\nVerifying migration...');
  const { count, error: countError } = await supabase
    .from('markers')
    .select('*', { count: 'exact', head: true });

  if (countError) {
    console.error('Error verifying migration:', countError);
  } else {
    console.log(`✓ Database contains ${count} markers`);
  }

  // Step 7: Summary by category
  const { data: categoryCounts } = await supabase
    .from('markers')
    .select('category')
    .then(({ data }) => {
      const counts: Record<string, number> = {};
      data?.forEach(({ category }: any) => {
        counts[category] = (counts[category] || 0) + 1;
      });
      return { data: counts };
    });

  if (categoryCounts) {
    console.log('\nDatabase marker counts by category:');
    Object.entries(categoryCounts).forEach(([category, count]) => {
      console.log(`  ${category.padEnd(10)}: ${count}`);
    });
  }

  console.log('\n✅ Migration finished successfully!');
  console.log(`\nBackup saved to: ${jsonBackupPath}`);
}

/**
 * Clear all markers from database (for testing)
 */
async function clearMarkers() {
  console.log('⚠️  Clearing all markers from database...');

  const { error } = await supabase.from('markers').delete().neq('id', '');

  if (error) {
    console.error('Error clearing markers:', error);
  } else {
    console.log('✓ All markers cleared');
  }
}

/**
 * Show database statistics
 */
async function showStats() {
  console.log('Fetching database statistics...\n');

  // Total count
  const { count: totalCount } = await supabase
    .from('markers')
    .select('*', { count: 'exact', head: true });

  console.log(`Total markers: ${totalCount}\n`);

  // By category
  const { data: markers } = await supabase.from('markers').select('category, lang');

  if (markers) {
    const categoryStats: Record<string, number> = {};
    const langStats: Record<string, number> = {};

    markers.forEach((m: any) => {
      categoryStats[m.category] = (categoryStats[m.category] || 0) + 1;
      langStats[m.lang] = (langStats[m.lang] || 0) + 1;
    });

    console.log('By category:');
    Object.entries(categoryStats).forEach(([cat, count]) => {
      console.log(`  ${cat.padEnd(10)}: ${count}`);
    });

    console.log('\nBy language:');
    Object.entries(langStats).forEach(([lang, count]) => {
      console.log(`  ${lang.padEnd(6)}: ${count}`);
    });
  }

  // Recent updates
  const { data: recentMarkers } = await supabase
    .from('markers')
    .select('id, updated_at')
    .order('updated_at', { ascending: false })
    .limit(5);

  if (recentMarkers && recentMarkers.length > 0) {
    console.log('\nRecently updated:');
    recentMarkers.forEach((m: any) => {
      const date = new Date(m.updated_at).toLocaleString();
      console.log(`  ${m.id.padEnd(40)} - ${date}`);
    });
  }
}

// CLI handler
const command = process.argv[2];

switch (command) {
  case 'migrate':
    migrateMarkers().catch(console.error);
    break;
  case 'clear':
    clearMarkers().catch(console.error);
    break;
  case 'stats':
    showStats().catch(console.error);
    break;
  default:
    console.log(`
Neural Marker Engine - Migration Tool

Usage:
  npm run migrate              Migrate YAML markers to Supabase
  npm run migrate clear        Clear all markers from database
  npm run migrate stats        Show database statistics

Environment variables required:
  SUPABASE_URL                 Your Supabase project URL
  SUPABASE_SERVICE_ROLE_KEY    Service role key (not anon key)
  MARKERS_BASE_PATH            Path to marker directories (default: ../)
    `);
}
