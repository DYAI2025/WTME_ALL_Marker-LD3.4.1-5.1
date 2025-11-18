/* eslint-disable @typescript-eslint/no-explicit-any */
import { pipeline } from "@xenova/transformers";
export class MarkerEngine {
    registry;
    extractor;
    cache = new Map();
    constructor(registry) {
        this.registry = registry;
    }
    async init({ modelPath }) {
        globalThis.TRANSFORMERS_CACHE = modelPath;
        this.extractor = await pipeline("feature-extraction", "Xenova/all-MiniLM-L6-v2");
    }
    async embed(text) {
        const key = text.toLowerCase();
        const cached = this.cache.get(key);
        if (cached)
            return cached;
        const output = await this.extractor(key, { pooling: "mean", normalize: true });
        const vector = new Float32Array(output.data);
        this.cache.set(key, vector);
        return vector;
    }
    cosine(a, b) {
        let dot = 0;
        let na = 0;
        let nb = 0;
        for (let i = 0; i < a.length; i += 1) {
            const av = a[i];
            const bv = b[i];
            dot += av * bv;
            na += av * av;
            nb += bv * bv;
        }
        const denom = Math.sqrt(na) * Math.sqrt(nb) + 1e-9;
        return dot / denom;
    }
    async scoreSentence(sentence) {
        const vSentence = await this.embed(sentence);
        const hits = [];
        const workerPost = typeof globalThis.postMessage === "function" ? globalThis.postMessage.bind(globalThis) : null;
        for (const marker of this.registry) {
            const referenceParts = [marker.frame?.concept ?? ""];
            if (marker.frame?.signal?.length)
                referenceParts.push(...marker.frame.signal);
            if (marker.examples?.length)
                referenceParts.push(...marker.examples.slice(0, 5));
            const reference = referenceParts.join(" ; ").trim();
            if (!reference)
                continue;
            const vReference = await this.embed(reference);
            const score = this.cosine(vSentence, vReference);
            if (score >= 0.6) {
                hits.push({ id: marker.id, type: marker.type, score });
            }
            if (workerPost && score >= 0.53 && score < 0.6) {
                workerPost({ type: "uncertain", marker: marker.id, sentence, score });
            }
        }
        const atoHits = new Set(hits.filter((h) => h.type === "ATO").map((h) => h.id));
        const semHits = new Set();
        const cluHits = new Set();
        const registryById = new Map(this.registry.map((m) => [m.id, m]));
        for (const marker of this.registry) {
            if (marker.type !== "SEM" || !marker.composed_of?.length)
                continue;
            const required = marker.composed_of.filter((id) => atoHits.has(id));
            if (required.length >= Math.min(2, marker.composed_of.length)) {
                semHits.add(marker.id);
            }
        }
        for (const marker of this.registry) {
            if (marker.type !== "CLU" || !marker.composed_of?.length)
                continue;
            const semNeeded = marker.composed_of.length;
            const active = marker.composed_of.filter((id) => semHits.has(id));
            if (active.length >= Math.max(1, Math.floor(semNeeded * 0.6))) {
                cluHits.add(marker.id);
            }
        }
        // propagate composed chain: if CLU nodes have composed_of referencing SEM or CLU
        for (const cluId of Array.from(cluHits)) {
            const marker = registryById.get(cluId);
            if (!marker?.composed_of)
                continue;
            for (const id of marker.composed_of) {
                if (registryById.get(id)?.type === "SEM")
                    semHits.add(id);
            }
        }
        const result = {
            atoTriggered: Array.from(atoHits),
            semTriggered: Array.from(semHits),
            cluTriggered: Array.from(cluHits),
            kwAtoHits: Array.from(atoHits),
            scores: hits,
        };
        return result;
    }
}
let engine = null;
onmessage = async (event) => {
    const { cmd, payload } = event.data ?? {};
    if (cmd === "init") {
        engine = new MarkerEngine(payload.registry);
        await engine.init({ modelPath: payload.modelPath });
        const workerPost = typeof globalThis.postMessage === "function" ? globalThis.postMessage.bind(globalThis) : null;
        workerPost?.({ type: "ready" });
        return;
    }
    if (cmd === "score" && engine) {
        const res = await engine.scoreSentence(payload.sentence);
        const workerPost = typeof globalThis.postMessage === "function" ? globalThis.postMessage.bind(globalThis) : null;
        if (!workerPost)
            return;
        workerPost({
            type: "result",
            id: payload.id,
            tabId: payload.tabId,
            sentence: payload.sentence,
            result: res,
        });
    }
};
