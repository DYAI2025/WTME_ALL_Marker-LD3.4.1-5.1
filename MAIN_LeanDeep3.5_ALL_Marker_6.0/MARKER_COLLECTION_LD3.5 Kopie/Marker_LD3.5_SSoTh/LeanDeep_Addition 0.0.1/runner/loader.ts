import fs from "node:fs/promises";
import path from "node:path";
import Ajv from "ajv";

export type Marker = any;

const ajv = new Ajv({ allErrors: true });

// Registry populated by load_manifest
export let registry: Marker[] = [];
export function get_registry(): Marker[] {
  return registry;
}

export async function load_manifest(paths: string[]): Promise<void> {
  const schemaPath = paths.find((p) =>
    p.endsWith("schemas/ld314_marker.schema.json")
  );
  let validate: any = null;
  if (schemaPath) {
    const schema = JSON.parse(await fs.readFile(schemaPath, "utf8"));
    validate = ajv.compile(schema);
  }
  registry = [];
  for (const p of paths) {
    const stat = await fs.stat(p).catch(() => null);
    if (!stat) continue;
    if (stat.isDirectory()) {
      const files = await fs.readdir(p);
      for (const f of files) {
        if (!f.endsWith(".yaml") && !f.endsWith(".yml")) continue;
        const content = await fs.readFile(path.join(p, f), "utf8");
        const m = parseYAML(content);
        if (validate && !validate(m)) {
          // eslint-disable-next-line no-console
          console.warn("Schema validation failed for", f, validate.errors);
        }
        registry.push(m);
      }
    }
  }
}

function parseYAML(y: string): any {
  // lightweight parse: prefer yaml parser
  try {
    const yaml = require("yaml");
    return yaml.parse(y);
  } catch {
    // fallback naive parse for JSON-compatible YAML
    return JSON.parse(y);
  }
}
