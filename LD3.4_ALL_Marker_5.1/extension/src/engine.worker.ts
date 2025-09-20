import { pipeline } from "@xenova/transformers";

type FamilyCfg = { atos: string[]; sems: string[]; hint_id: string };
let FAMILIES: Record<string, FamilyCfg> = {};

type Frame = { concept: string; signal?: string[] };
type RegItem = {
  id: string;
  type: "ATO" | "SEM" | "CLU";
  frame: Frame;
  examples?: string[];
  composed_of?: string[];
  negation_guard?: { regex: string; window?: number };
};

export class MarkerEngine {
  private extractor: any;
  private reg: RegItem[] = [];

  async init({ modelPath, registry, families }: { modelPath: string; registry: RegItem[]; families: Record<string, FamilyCfg> }) {
    (globalThis as any).TRANSFORMERS_CACHE = modelPath;
    this.extractor = await pipeline("feature-extraction", "Xenova/all-MiniLM-L6-v2");
    this.reg = registry;
    FAMILIES = families;
  }

  private async embed(text: string): Promise<Float32Array> {
    const out = await this.extractor(text, { pooling: "mean", normalize: true });
    return out.data as Float32Array;
  }

  private cos(a: Float32Array, b: Float32Array): number {
    let s = 0;
    for (let i = 0; i < a.length; i++) s += a[i] * b[i];
    return s;
  }

  private negated(sentence: string, m: RegItem) {
    if (!("negation_guard" in (m as any))) return false;
    const g = (m as any).negation_guard as { regex: string; window?: number };
    const guard = new RegExp(g.regex, "i");
    if (!guard.test(sentence)) return false;
    const sig = (m.frame.signal || []).find(s => new RegExp(`\\b${s}\\b`, "i").test(sentence));
    if (!sig) return false;
    const idxN = sentence.toLowerCase().search(guard);
    const idxS = sentence.toLowerCase().indexOf(sig.toLowerCase());
    const approxCharsPerToken = 10;
    const win = (g.window ?? 3) * approxCharsPerToken;
    return Math.abs(idxN - idxS) <= win;
  }

  private stemOf(id: string) { return id.replace(/_(WORD|PHRASE|VERB)$/, ""); }

  async scoreSentence(sentence: string) {
    const vSent = await this.embed(sentence);
    const hits: { id: string; type: string; score: number }[] = [];

    for (const m of this.reg) {
      const ref = [m.frame.concept, ...(m.frame.signal || []), ...(m.examples || [])].join(" ; ");
      const v = await this.embed(ref);
      const sc = this.cos(vSent, v);
      if (m.type === "ATO") {
        if (sc >= 0.60 && !this.negated(sentence, m)) hits.push({ id: m.id, type: m.type, score: sc });
        else if (sc >= 0.53 && sc < 0.60) (globalThis as any).postMessage?.({ type: "uncertain", sentence, marker: m.id, score: sc });
      } else if (sc >= 0.60) {
        hits.push({ id: m.id, type: m.type, score: sc });
      }
    }

    // ATO Dedupe: Cooldown pro Satz und max. 2 Credits pro Lemma
    const atoIds = hits.filter(h => h.type === "ATO").map(h => h.id);
    const seen = new Set<string>();
    const stems = new Map<string, number>();
    const atoDedup = atoIds.filter(id => {
      if (seen.has(id)) return false; seen.add(id);
      const st = this.stemOf(id); const c = stems.get(st) || 0; if (c >= 2) return false; stems.set(st, c + 1); return true;
    });
    const atoEffective = new Set(atoDedup);

    // SEM-Regel: mindestens 2 aus composed_of (oder alles, falls nur eins definiert)
    const semTriggered: string[] = this.reg
      .filter(r => r.type === "SEM" && r.composed_of?.length)
      .filter(s => s.composed_of!.filter(x => atoEffective.has(x)).length >= Math.min(2, s.composed_of!.length))
      .map(s => s.id);

    // Fallback Familien-Hints
    const hints: string[] = [];
    for (const fam of Object.values(FAMILIES)) {
      const atoHits = fam.atos.filter(a => atoEffective.has(a));
      const semHits = fam.sems.filter(s => semTriggered.includes(s));
      if (atoHits.length >= 3 && semHits.length === 0) hints.push(fam.hint_id);
    }

    // CLU: Hints als schwache SEM akzeptieren
    const semUnion = new Set([...semTriggered, ...hints]);
    const cluTriggered: string[] = this.reg
      .filter(r => r.type === "CLU" && r.composed_of?.length)
      .filter(c => c.composed_of!.filter(x => semUnion.has(x)).length >= Math.max(1, Math.floor((c.composed_of!.length || 1) * 0.6)))
      .map(c => c.id);

    return { ato: Array.from(atoEffective), sem: Array.from(semUnion), clu: cluTriggered, scores: hits };
  }
}

let engine: MarkerEngine | null = null;
self.onmessage = async (e: MessageEvent) => {
  const { cmd, payload } = e.data || {};
  if (cmd === "init") {
    engine = new MarkerEngine();
    await engine.init(payload);
    (self as any).postMessage({ type: "ready" });
  } else if (cmd === "score" && engine) {
    const res = await engine.scoreSentence(payload.sentence);
    (self as any).postMessage({ type: "scored", payload: res });
  }
};


