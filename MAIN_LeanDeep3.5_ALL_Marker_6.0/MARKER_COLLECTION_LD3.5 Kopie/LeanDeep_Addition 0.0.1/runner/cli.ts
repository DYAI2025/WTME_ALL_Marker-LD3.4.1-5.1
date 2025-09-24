#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import { load_manifest } from "./loader";
import { detect_ato } from "./detect";
import { compose_sem } from "./compose";
import { aggregate_clu } from "./aggregate";
import { contextual_rescan } from "./intuition";
import { explain } from "./explain";

const argv = await yargs(hideBin(process.argv))
  .command("run", "Analyze text with markers", (y) =>
    y
      .option("markers", { type: "string", demandOption: true })
      .option("in", { type: "string", demandOption: true })
      .option("out", { type: "string", demandOption: true })
      .option("use-intuition", { type: "boolean", default: false })
  )
  .help()
  .parse();

if ((argv as any)._?.[0] === "run") {
  const markersRoot = path.resolve(argv.markers as string);
  const textPath = path.resolve(argv.in as string);
  const outPath = path.resolve(argv.out as string);
  await load_manifest([
    path.join(markersRoot, "atomics"),
    path.join(markersRoot, "semantics"),
    path.join(markersRoot, "clusters"),
  ]);
  const text = await fs.readFile(textPath, "utf8");
  const ato = await detect_ato(text);
  const sem = await compose_sem(ato);
  let clu = await aggregate_clu(sem);
  if (argv["use-intuition"]) {
    clu = await contextual_rescan(clu);
  }
  const hits = [...ato, ...sem, ...clu];
  const ex = await explain(hits);
  await fs.writeFile(
    outPath,
    JSON.stringify({ hits, explainability: ex }, null, 2)
  );
}
