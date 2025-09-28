import fg from "fast-glob";
import fs from "fs/promises";
import path from "path";
import yaml from "js-yaml";

type Marker = {
  id: string;
  type: string;
  frame?: unknown;
  examples?: string[];
  negatives?: string[];
  composed_of?: string[];
};

async function loadMarkers(): Promise<Array<Marker & { source: string }>> {
  const files = await fg("markers/**/*.y?(a)ml", { dot: false });
  const markers: Array<Marker & { source: string }> = [];
  for (const file of files) {
    const raw = yaml.load(await fs.readFile(file, "utf8"));
    if (!raw || typeof raw !== "object") continue;
    const marker = raw as Marker;
    if (!marker.id || !marker.type) {
      console.warn(`überspringe ${file}, fehlt id oder type`);
      continue;
    }
    markers.push({ ...marker, source: file });
  }
  return markers;
}

async function writeRegistry(markers: Array<Marker & { source: string }>) {
  await fs.mkdir("dist", { recursive: true });
  const registryPath = path.join("dist", "marker_registry.json");
  await fs.writeFile(registryPath, JSON.stringify(markers, null, 2), "utf8");
  console.log(`Registry geschrieben → ${registryPath}`);
}

async function main() {
  const markers = await loadMarkers();
  await writeRegistry(markers);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
