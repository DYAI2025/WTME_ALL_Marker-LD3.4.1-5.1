import fs from "fs/promises";
import { JSDOM } from "jsdom";
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore - reuse worker implementation
import { MarkerEngine } from "../extension/src/engine.worker";
import registry from "../dist/marker_registry.json" assert { type: "json" };

function splitSentences(text: string): string[] {
  return text
    .split(/(?<=[.!?])\s+/)
    .map((part) => part.trim())
    .filter((part) => part.length > 0);
}

async function main() {
  const urls = process.argv.slice(2);
  if (urls.length === 0) {
    console.error("Usage: npm run crawl -- <url> [<url> ...]");
    process.exit(1);
  }
  const engine = new (MarkerEngine as any)(registry);
  await engine.init({ modelPath: "models/all-MiniLM-L6-v2" });
  const output: string[] = [];

  for (const url of urls) {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        console.warn(`Skip ${url}: HTTP ${response.status}`);
        continue;
      }
      const html = await response.text();
      const dom = new JSDOM(html);
      const blocks = Array.from(dom.window.document.querySelectorAll("p,li"));
      const text = blocks
        .map((node) => node.textContent?.trim() ?? "")
        .filter((value) => value.length > 0)
        .join("\n");
      for (const sentence of splitSentences(text)) {
        const result = await engine.scoreSentence(sentence);
        output.push(
          JSON.stringify({
            url,
            text: sentence,
            prediction: { sem: result.semTriggered, clu: result.cluTriggered, ato: result.atoTriggered },
          }),
        );
      }
    } catch (error) {
      console.warn(`Fehler bei ${url}:`, error);
    }
  }

  await fs.mkdir("dist", { recursive: true });
  const target = "dist/crawl_labeled.jsonl";
  await fs.writeFile(target, output.join("\n"), "utf8");
  console.log(`Label-Datei → ${target}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
