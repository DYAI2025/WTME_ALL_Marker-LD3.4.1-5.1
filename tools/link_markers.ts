import fg from "fast-glob";
import fs from "fs/promises";
import path from "path";
import yaml from "js-yaml";

type Marker = {
  id: string;
  type: "ATO" | "SEM" | "CLU" | "MEMA";
  frame?: { concept?: string; signal?: string[] };
  examples?: string[];
  negatives?: string[];
  composed_of?: string[];
};

type ReportEntry = {
  id: string;
  type: string;
  composed_of?: string[];
  added?: string[];
  removed?: string[];
};

const MARKER_GLOB = "markers/**/*.y?(a)ml";

function tokenize(parts: string[]): Set<string> {
  const tokens = new Set<string>();
  for (const part of parts) {
    part
      .toLowerCase()
      .replace(/[^\p{L}\p{N}]+/gu, " ")
      .split(/\s+/)
      .filter(Boolean)
      .forEach((token) => tokens.add(token));
  }
  return tokens;
}

function overlapScore(base: Set<string>, candidate: Set<string>): number {
  let score = 0;
  candidate.forEach((token) => {
    if (base.has(token)) score += 1;
  });
  return score;
}

async function loadMarkers(): Promise<Map<string, { file: string; marker: Marker; tokens: Set<string> }>> {
  const files = await fg(MARKER_GLOB, { dot: false });
  const result = new Map<string, { file: string; marker: Marker; tokens: Set<string> }>();
  for (const file of files) {
    const raw = yaml.load(await fs.readFile(file, "utf8")) as Marker;
    if (!raw?.id || !raw.type) continue;
    const parts = [raw.frame?.concept ?? ""];
    if (raw.frame?.signal) parts.push(...raw.frame.signal);
    if (raw.examples) parts.push(...raw.examples);
    const tokens = tokenize(parts);
    result.set(raw.id, { file, marker: raw, tokens });
  }
  return result;
}

async function writeMarker(file: string, marker: Marker) {
  const out = yaml.dump(marker, { lineWidth: 100, sortKeys: false });
  await fs.writeFile(file, out, "utf8");
}

async function ensureDirectories() {
  await fs.mkdir("build", { recursive: true });
}

async function main() {
  await ensureDirectories();
  const index = await loadMarkers();
  const report: ReportEntry[] = [];

  const allMarkers = Array.from(index.values());
  const atoItems = allMarkers.filter(({ marker }) => marker.type === "ATO");
  const semItems = allMarkers.filter(({ marker }) => marker.type === "SEM");

  for (const { file, marker } of allMarkers) {
    const original = Array.isArray(marker.composed_of) ? [...marker.composed_of] : [];
    const cleaned = original.filter((id) => index.has(id));
    const missing = original.filter((id) => !index.has(id));

    if (missing.length) {
      marker.composed_of = cleaned;
    }

    if ((!marker.composed_of || marker.composed_of.length === 0) && marker.type !== "ATO" && marker.type !== "MEMA") {
      const candidates = marker.type === "SEM" ? atoItems : semItems;
      const baseTokens = tokenize([
        marker.frame?.concept ?? "",
        ...(marker.frame?.signal ?? []),
        ...(marker.examples ?? []),
      ]);
      const scored = candidates
        .map((item) => ({ id: item.marker.id, score: overlapScore(baseTokens, item.tokens) }))
        .filter((entry) => entry.score > 0)
        .sort((a, b) => b.score - a.score)
        .slice(0, 3)
        .map((entry) => entry.id);
      if (scored.length > 0) {
        marker.composed_of = scored;
      }
    }

    const updated = marker.composed_of ?? [];
    const added = updated.filter((id) => !original.includes(id));
    const removed = original.filter((id) => !updated.includes(id));
    if (added.length > 0 || removed.length > 0) {
      await writeMarker(file, marker);
    }
    report.push({ id: marker.id, type: marker.type, composed_of: updated, added: added.length ? added : undefined, removed: removed.length ? removed : undefined });
  }

  await fs.writeFile(path.join("build", "link_report.json"), JSON.stringify(report, null, 2), "utf8");
  console.log("Linking complete. Report → build/link_report.json");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
