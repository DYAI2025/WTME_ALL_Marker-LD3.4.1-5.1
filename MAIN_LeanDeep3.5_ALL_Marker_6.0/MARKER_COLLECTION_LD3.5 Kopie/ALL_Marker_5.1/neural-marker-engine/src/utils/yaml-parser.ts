import * as fs from 'fs';
import * as path from 'path';
import YAML from 'yaml';
import { Marker, MarkerCategory, AtomicMarker, SemanticMarker, ClusterMarker, MetaMarker } from '../types/marker.types.js';

/**
 * Parse a YAML marker file into a typed Marker object
 */
export function parseMarkerFile(filePath: string): Marker | null {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const parsed = YAML.parse(content);

    if (!parsed || !parsed.id) {
      console.warn(`Invalid marker file (no id): ${filePath}`);
      return null;
    }

    // Normalize version field
    const version = parsed.version || parsed.schema_version || '3.4';

    // Normalize category
    const category = parsed.category?.toUpperCase() as MarkerCategory;
    if (!['ATOMIC', 'SEMANTIC', 'CLUSTER', 'META'].includes(category)) {
      console.warn(`Invalid category ${category} in ${filePath}`);
      return null;
    }

    // Ensure frame exists
    if (!parsed.frame) {
      console.warn(`Missing frame in ${filePath}`);
      return null;
    }

    // Build base marker
    const baseMarker = {
      id: parsed.id,
      schema: parsed.schema || 'LeanDeep',
      version,
      namespace: parsed.namespace,
      lang: parsed.lang || 'de',
      category,
      description: parsed.description || '',
      frame: parsed.frame,
      examples: parsed.examples,
      tags: parsed.tags,
      metadata: parsed.metadata,
    };

    // Type-specific fields
    switch (category) {
      case 'ATOMIC':
        return {
          ...baseMarker,
          category: 'ATOMIC',
          pattern: parsed.pattern || [],
          activation_logic: parsed.activation_logic,
        } as AtomicMarker;

      case 'SEMANTIC':
        return {
          ...baseMarker,
          category: 'SEMANTIC',
          composed_of: parsed.composed_of || [],
          activation_logic: parsed.activation_logic,
          scoring: parsed.scoring,
        } as SemanticMarker;

      case 'CLUSTER':
        return {
          ...baseMarker,
          category: 'CLUSTER',
          composed_of: parsed.composed_of,
          components: parsed.components,
          activation: parsed.activation,
          window: parsed.window,
          scoring: parsed.scoring,
          pattern: parsed.pattern,
        } as ClusterMarker;

      case 'META':
        return {
          ...baseMarker,
          category: 'META',
          components: parsed.components || parsed.composed_of || [],
          pattern: parsed.pattern,
        } as MetaMarker;

      default:
        console.warn(`Unknown category: ${category}`);
        return null;
    }
  } catch (error) {
    console.error(`Error parsing ${filePath}:`, error);
    return null;
  }
}

/**
 * Recursively find all YAML files in a directory
 */
export function findYamlFiles(dir: string): string[] {
  const files: string[] = [];

  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        files.push(...findYamlFiles(fullPath));
      } else if (entry.isFile() && (entry.name.endsWith('.yaml') || entry.name.endsWith('.yml'))) {
        files.push(fullPath);
      }
    }
  } catch (error) {
    console.error(`Error reading directory ${dir}:`, error);
  }

  return files;
}

/**
 * Load all markers from a directory structure
 */
export function loadAllMarkers(basePath: string): Marker[] {
  const markers: Marker[] = [];

  // Define directories to scan
  const directories = [
    path.join(basePath, 'ATO_atomic'),
    path.join(basePath, 'SEM_semantic'),
    path.join(basePath, 'CLU_cluster'),
    path.join(basePath, 'MEMA_meta'),
  ];

  for (const dir of directories) {
    if (!fs.existsSync(dir)) {
      console.warn(`Directory not found: ${dir}`);
      continue;
    }

    const files = findYamlFiles(dir);
    console.log(`Found ${files.length} YAML files in ${path.basename(dir)}`);

    for (const file of files) {
      const marker = parseMarkerFile(file);
      if (marker) {
        markers.push(marker);
      }
    }
  }

  return markers;
}

/**
 * Validate marker dependencies
 * Returns array of missing marker IDs
 */
export function validateMarkerDependencies(markers: Marker[]): string[] {
  const markerIds = new Set(markers.map(m => m.id));
  const missingDeps: Set<string> = new Set();

  for (const marker of markers) {
    let dependencies: string[] = [];

    switch (marker.category) {
      case 'SEMANTIC':
        dependencies = marker.composed_of;
        break;
      case 'CLUSTER':
        if (marker.composed_of) {
          dependencies = marker.composed_of.flatMap(c => c.marker_ids);
        } else if (marker.components) {
          dependencies = marker.components;
        }
        break;
      case 'META':
        dependencies = marker.components;
        break;
    }

    for (const dep of dependencies) {
      if (!markerIds.has(dep)) {
        missingDeps.add(dep);
      }
    }
  }

  return Array.from(missingDeps);
}

/**
 * Group markers by category
 */
export function groupMarkersByCategory(markers: Marker[]): Record<MarkerCategory, Marker[]> {
  const grouped: Record<MarkerCategory, Marker[]> = {
    ATOMIC: [],
    SEMANTIC: [],
    CLUSTER: [],
    META: [],
  };

  for (const marker of markers) {
    grouped[marker.category].push(marker);
  }

  return grouped;
}

/**
 * Export markers to JSON file
 */
export function exportMarkersToJson(markers: Marker[], outputPath: string): void {
  const data = {
    version: '3.4',
    exported_at: new Date().toISOString(),
    count: markers.length,
    markers,
  };

  fs.writeFileSync(outputPath, JSON.stringify(data, null, 2), 'utf-8');
  console.log(`Exported ${markers.length} markers to ${outputPath}`);
}
