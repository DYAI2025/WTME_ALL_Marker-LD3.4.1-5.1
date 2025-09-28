import fs from "fs/promises";
import path from "path";
import yaml from "js-yaml";
import fg from "fast-glob";

type Suggestion = {
  marker: string;
  text: string;
  score: number;
};

type MarkerDoc = {
  id?: string;
  examples?: string[];
};

async function main() {
  const suggestionsPath = "dist/autogen_examples.jsonl";
  let content = "";
  try {
    content = await fs.readFile(suggestionsPath, "utf8");
  } catch (error) {
    console.error(`Keine Vorschläge gefunden (${suggestionsPath})`);
    process.exit(1);
  }

  const suggestions = content
    .trim()
    .split("\n")
    .map((line) => JSON.parse(line) as Suggestion)
    .filter((entry) => typeof entry.marker === "string" && typeof entry.text === "string" && typeof entry.score === "number");

  const grouped = new Map<string, Suggestion[]>();
  for (const suggestion of suggestions) {
    if (suggestion.score < 0.62) continue;
    const bucket = grouped.get(suggestion.marker) ?? [];
    bucket.push(suggestion);
    grouped.set(suggestion.marker, bucket);
  }

  if (grouped.size === 0) {
    console.log("Keine anwendbaren Vorschläge");
    return;
  }

  const files = await fg("markers/**/*.y?(a)ml");
  const index = new Map<string, string>();
  for (const file of files) {
    const doc = yaml.load(await fs.readFile(file, "utf8")) as MarkerDoc;
    if (doc?.id) index.set(doc.id, file);
  }

  for (const [markerId, entries] of grouped) {
    const targetFile = index.get(markerId);
    if (!targetFile) {
      console.warn(`Keine Marker-Datei für ${markerId}`);
      continue;
    }
    const doc = yaml.load(await fs.readFile(targetFile, "utf8")) as MarkerDoc;
    const examples = new Set<string>(doc.examples ?? []);
    entries
      .sort((a, b) => b.score - a.score)
      .slice(0, 10)
      .forEach((entry) => examples.add(entry.text));
    doc.examples = Array.from(examples);
    const outPath = targetFile.replace(/\.ya?ml$/, ".autogen.yml");
    await fs.writeFile(outPath, yaml.dump(doc, { lineWidth: 100, sortKeys: false }), "utf8");
    console.log(`Schreibe Vorschlagsdatei → ${outPath}`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
