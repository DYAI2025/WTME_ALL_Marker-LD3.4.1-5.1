import express from "express";
import bodyParser from "body-parser";
import type { AnalyzeReq, MarkerHit } from "./types";
import { load_manifest } from "./loader";
import { detect_ato } from "./detect";
import { compose_sem } from "./compose";
import { aggregate_clu } from "./aggregate";
import { contextual_rescan } from "./intuition";
import { explain } from "./explain";

const app = express();
app.use(bodyParser.json());

app.post("/analyze", async (req, res) => {
  const payload = req.body as AnalyzeReq;
  await load_manifest(payload.markerPaths);
  const ato = await detect_ato(payload.text);
  const sem = await compose_sem(ato);
  let clu = await aggregate_clu(sem);
  if (payload.options?.useIntuition) {
    clu = await contextual_rescan(clu);
  }
  const hits: MarkerHit[] = [...ato, ...sem, ...clu];
  const ex = await explain(hits);
  res.json({ hits, explainability: ex });
});

export function start(port = 8080) {
  app.listen(port, () => console.log("LD314 server on", port));
}
