import fs from "fs/promises";
import path from "path";
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore - reuse engine worker class for Node execution
import { MarkerEngine } from "../extension/src/engine.worker";
import registry from "../dist/marker_registry.json" assert { type: "json" };

type ResultCounts = Record<string, { tp: number; fp: number; fn: number }>;

async function main() {
  const devsetPath = path.resolve("dist", "devset.jsonl");
  const lines = (await fs.readFile(devsetPath, "utf8")).trim().split("\n");
  const dataset = lines.map((line) => JSON.parse(line) as { text: string; gold: string[] });
  const engine = new (MarkerEngine as any)(registry);
  await engine.init({ modelPath: "models/all-MiniLM-L6-v2" });

  const counts: ResultCounts = {};
  const ensure = (key: string) => {
    if (!counts[key]) counts[key] = { tp: 0, fp: 0, fn: 0 };
    return counts[key];
  };

  for (const entry of dataset) {
    const prediction = await engine.scoreSentence(entry.text);
    const predicted = new Set<string>([
      ...(prediction.semTriggered ?? []),
      ...(prediction.cluTriggered ?? []),
      ...(prediction.kwAtoHits ?? []),
    ]);
    const gold = new Set<string>(entry.gold);
    const universe = new Set<string>([...predicted, ...gold]);
    universe.delete("NONE");
    for (const label of universe) {
      const slot = ensure(label);
      const isPred = predicted.has(label);
      const isGold = gold.has(label);
      if (isPred && isGold) slot.tp += 1;
      else if (isPred && !isGold) slot.fp += 1;
      else if (!isPred && isGold) slot.fn += 1;
    }
  }

  for (const [label, score] of Object.entries(counts)) {
    const precision = score.tp / (score.tp + score.fp || 1);
    const recall = score.tp / (score.tp + score.fn || 1);
    const f1 = (2 * precision * recall) / (precision + recall || 1);
    console.log(`${label}\tP=${precision.toFixed(2)}\tR=${recall.toFixed(2)}\tF1=${f1.toFixed(2)}`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
