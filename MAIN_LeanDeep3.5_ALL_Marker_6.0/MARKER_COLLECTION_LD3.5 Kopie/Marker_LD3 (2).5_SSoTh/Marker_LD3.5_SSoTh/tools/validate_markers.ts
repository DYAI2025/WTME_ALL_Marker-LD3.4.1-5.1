import fg from "fast-glob";
import fs from "fs/promises";
import yaml from "js-yaml";

type Marker = {
  id?: string;
  type?: "ATO" | "SEM" | "CLU" | "MEMA";
  frame?: { concept?: string; narrative?: string; signal?: string[] };
  examples?: string[];
  negatives?: string[];
  composed_of?: string[];
};

function err(message: string) {
  console.error("ERR:", message);
}

function warn(message: string) {
  console.warn("WARN:", message);
}

(async () => {
  const files = await fg(["markers/**/*.y?(a)ml"], { dot: false });
  let ok = true;
  for (const file of files) {
    const raw = yaml.load(await fs.readFile(file, "utf8")) as Marker | null;
    if (!raw || typeof raw !== "object") {
      err(`${file}: YAML leer oder ungültig`);
      ok = false;
      continue;
    }
    if (!raw.id) {
      err(`${file}: fehlt id`);
      ok = false;
    }
    if (!raw.type) {
      err(`${file}: fehlt type`);
      ok = false;
    }
    if (!raw.frame?.concept) {
      err(`${file}: frame.concept fehlt`);
      ok = false;
    }
    const positive = raw.examples?.length ?? 0;
    const negative = raw.negatives?.length ?? 0;
    if (raw.type === "ATO" && positive < 20) {
      warn(`${raw.id}: nur ${positive} Positivbeispiele (>=20 empfohlen)`);
    }
    if (raw.type === "SEM" && positive < 20) {
      warn(`${raw.id}: nur ${positive} Positivbeispiele (>=30 empfohlen)`);
    }
    if (raw.type !== "MEMA" && negative > 0 && negative < Math.min(20, positive)) {
      warn(`${raw.id}: Negativbeispiele ${negative}/${positive} relativ niedrig`);
    }
    if (raw.type && raw.type !== "ATO" && !raw.composed_of) {
      warn(`${raw.id}: composed_of fehlt (prüfen)`);
    }
  }
  if (!ok) process.exit(1);
  console.log("Marker-Validierung OK");
})();
