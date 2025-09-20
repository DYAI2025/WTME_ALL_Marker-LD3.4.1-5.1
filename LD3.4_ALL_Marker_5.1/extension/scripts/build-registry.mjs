import { promises as fs } from 'node:fs';
import path from 'node:path';
import yaml from 'yaml';

const root = path.resolve(process.cwd());
const markersRoot = path.join(root, 'ALL_Marker_5.1');
const outDir = path.join(root, 'extension', 'dist');

async function readYamlFile(p) {
  const raw = await fs.readFile(p, 'utf8');
  return yaml.parse(raw);
}

async function collect(dir) {
  const items = await fs.readdir(dir);
  const out = [];
  for (const it of items) {
    const full = path.join(dir, it);
    const stat = await fs.stat(full);
    if (stat.isDirectory()) {
      out.push(...await collect(full));
    } else if (/\.ya?ml$/i.test(it)) {
      try { out.push(await readYamlFile(full)); } catch { /* ignore */ }
    }
  }
  return out;
}

async function main(){
  await fs.mkdir(outDir, { recursive: true });
  const registry = await collect(markersRoot);
  await fs.writeFile(path.join(outDir,'registry.json'), JSON.stringify(registry, null, 2));
}

main().catch(e=>{ console.error(e); process.exit(1); });


