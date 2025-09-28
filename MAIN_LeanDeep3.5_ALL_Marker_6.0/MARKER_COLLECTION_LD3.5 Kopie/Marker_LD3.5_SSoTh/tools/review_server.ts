import express from "express";
import cors from "cors";
import bodyParser from "body-parser";
import fs from "fs/promises";
import path from "path";
import yaml from "js-yaml";
import fg from "fast-glob";

const PORT = Number(process.env.PORT ?? 5173);
const app = express();
app.use(cors());
app.use(bodyParser.json());

const ROOT = process.cwd();
const EX_FILE = path.join(ROOT, "dist/autogen_examples.jsonl");
const STATE_FILE = path.join(ROOT, "dist/review_state.json");
const MARKERS_GLOB = "markers/**/*.y?(a)ml";

type Example = { marker: string; text: string; score?: number; url?: string };
type StateRow = { marker: string; text: string; accepted: boolean; ts: number };
async function readExamples(): Promise<Example[]> {
  try {
    const raw = await fs.readFile(EX_FILE, "utf8");
    return raw
      .trim()
      .split("\n")
      .filter(Boolean)
      .map((line) => JSON.parse(line) as Example);
  } catch {
    return [];
  }
}

async function readState(): Promise<StateRow[]> {
  try {
    const raw = await fs.readFile(STATE_FILE, "utf8");
    return JSON.parse(raw) as StateRow[];
  } catch {
    return [];
  }
}

async function writeState(rows: StateRow[]) {
  await fs.writeFile(STATE_FILE, JSON.stringify(rows, null, 2), "utf8");
}

async function findMarkerFile(markerId: string): Promise<string | null> {
  const files = await fg(MARKERS_GLOB, { dot: false });
  for (const file of files) {
    try {
      const doc = yaml.load(await fs.readFile(file, "utf8")) as any;
      if (doc?.id === markerId) return file;
    } catch {
      // ignorieren
    }
  }
  return null;
}

async function insertExample(markerId: string, text: string): Promise<{ file?: string; inserted: boolean; reason?: string }> {
  const file = await findMarkerFile(markerId);
  if (!file) return { inserted: false, reason: "Marker-Datei nicht gefunden" };
  const doc = (yaml.load(await fs.readFile(file, "utf8")) as any) ?? {};
  if (!Array.isArray(doc.examples)) doc.examples = [];
  if (doc.examples.includes(text)) return { file, inserted: false, reason: "Beispiel bereits vorhanden" };
  doc.examples.push(text);
  const out = yaml.dump(doc, { lineWidth: 100, sortKeys: false });
  await fs.writeFile(file, out, "utf8");
  return { file, inserted: true };
}

app.get("/", async (_req, res) => {
  res.setHeader("content-type", "text/html; charset=utf-8");
  const html = await fs.readFile(path.join(ROOT, "review_gui.html"), "utf8");
  res.send(html);
});

app.get("/api/examples", async (_req, res) => {
  const [examples, state] = await Promise.all([readExamples(), readState()]);
  const decided = new Set(state.map((row) => `${row.marker}::${row.text}`));
  const pending = examples.filter((ex) => !decided.has(`${ex.marker}::${ex.text}`));
  res.json(pending.slice(0, 200));
});

app.post("/api/decision", async (req, res) => {
  const example = req.body?.example as Example | undefined;
  const accepted = Boolean(req.body?.accepted);
  if (!example?.marker || !example?.text) {
    res.status(400).json({ ok: false, error: "invalid payload" });
    return;
  }

  const response: Record<string, unknown> = { ok: true, accepted };
  if (accepted) {
    response.merge = await insertExample(example.marker, example.text);
  }

  const state = await readState();
  state.push({ marker: example.marker, text: example.text, accepted, ts: Date.now() });
  await writeState(state);

  res.json(response);
});

app.listen(PORT, () => {
  console.log(`Review-GUI läuft auf http://localhost:${PORT}`);
});

export {};
