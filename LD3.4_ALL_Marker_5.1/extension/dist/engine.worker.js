import { pipeline } from '@xenova/transformers';

// extension/src/engine.worker.ts
var FAMILIES = {};
var MarkerEngine = class {
  constructor() {
    this.reg = [];
  }
  async init({ modelPath, registry, families }) {
    globalThis.TRANSFORMERS_CACHE = modelPath;
    this.extractor = await pipeline("feature-extraction", "Xenova/all-MiniLM-L6-v2");
    this.reg = registry;
    FAMILIES = families;
  }
  async embed(text) {
    const out = await this.extractor(text, { pooling: "mean", normalize: true });
    return out.data;
  }
  cos(a, b) {
    let s = 0;
    for (let i = 0; i < a.length; i++) s += a[i] * b[i];
    return s;
  }
  negated(sentence, m) {
    if (!("negation_guard" in m)) return false;
    const g = m.negation_guard;
    const guard = new RegExp(g.regex, "i");
    if (!guard.test(sentence)) return false;
    const sig = (m.frame.signal || []).find((s) => new RegExp(`\\b${s}\\b`, "i").test(sentence));
    if (!sig) return false;
    const idxN = sentence.toLowerCase().search(guard);
    const idxS = sentence.toLowerCase().indexOf(sig.toLowerCase());
    const approxCharsPerToken = 10;
    const win = (g.window ?? 3) * approxCharsPerToken;
    return Math.abs(idxN - idxS) <= win;
  }
  stemOf(id) {
    return id.replace(/_(WORD|PHRASE|VERB)$/, "");
  }
  async scoreSentence(sentence) {
    const vSent = await this.embed(sentence);
    const hits = [];
    for (const m of this.reg) {
      const ref = [m.frame.concept, ...m.frame.signal || [], ...m.examples || []].join(" ; ");
      const v = await this.embed(ref);
      const sc = this.cos(vSent, v);
      if (m.type === "ATO") {
        if (sc >= 0.6 && !this.negated(sentence, m)) hits.push({ id: m.id, type: m.type, score: sc });
        else if (sc >= 0.53 && sc < 0.6) globalThis.postMessage?.({ type: "uncertain", sentence, marker: m.id, score: sc });
      } else if (sc >= 0.6) {
        hits.push({ id: m.id, type: m.type, score: sc });
      }
    }
    const atoIds = hits.filter((h) => h.type === "ATO").map((h) => h.id);
    const seen = /* @__PURE__ */ new Set();
    const stems = /* @__PURE__ */ new Map();
    const atoDedup = atoIds.filter((id) => {
      if (seen.has(id)) return false;
      seen.add(id);
      const st = this.stemOf(id);
      const c = stems.get(st) || 0;
      if (c >= 2) return false;
      stems.set(st, c + 1);
      return true;
    });
    const atoEffective = new Set(atoDedup);
    const semTriggered = this.reg.filter((r) => r.type === "SEM" && r.composed_of?.length).filter((s) => s.composed_of.filter((x) => atoEffective.has(x)).length >= Math.min(2, s.composed_of.length)).map((s) => s.id);
    const hints = [];
    for (const fam of Object.values(FAMILIES)) {
      const atoHits = fam.atos.filter((a) => atoEffective.has(a));
      const semHits = fam.sems.filter((s) => semTriggered.includes(s));
      if (atoHits.length >= 3 && semHits.length === 0) hints.push(fam.hint_id);
    }
    const semUnion = /* @__PURE__ */ new Set([...semTriggered, ...hints]);
    const cluTriggered = this.reg.filter((r) => r.type === "CLU" && r.composed_of?.length).filter((c) => c.composed_of.filter((x) => semUnion.has(x)).length >= Math.max(1, Math.floor((c.composed_of.length || 1) * 0.6))).map((c) => c.id);
    return { ato: Array.from(atoEffective), sem: Array.from(semUnion), clu: cluTriggered, scores: hits };
  }
};
var engine = null;
self.onmessage = async (e) => {
  const { cmd, payload } = e.data || {};
  if (cmd === "init") {
    engine = new MarkerEngine();
    await engine.init(payload);
    self.postMessage({ type: "ready" });
  } else if (cmd === "score" && engine) {
    const res = await engine.scoreSentence(payload.sentence);
    self.postMessage({ type: "scored", payload: res });
  }
};

export { MarkerEngine };
