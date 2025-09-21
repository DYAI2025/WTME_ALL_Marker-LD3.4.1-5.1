const registryUrl = chrome.runtime.getURL("dist/marker_registry.json");
const modelPath = chrome.runtime.getURL("dist/models");
let worker = null;
let workerReady = false;
async function bootstrap() {
    const response = await fetch(registryUrl);
    const registry = await response.json();
    worker = new Worker(chrome.runtime.getURL("dist/engine.worker.js"), { type: "module" });
    worker.onmessage = (event) => {
        const payload = event.data ?? {};
        if (payload.type === "ready") {
            workerReady = true;
            return;
        }
        if (payload.type === "uncertain") {
            logUncertain(payload);
            return;
        }
        if (payload.type === "result") {
            const targetTab = payload.tabId;
            if (typeof targetTab === "number") {
                chrome.tabs.sendMessage(targetTab, {
                    type: "marker-result",
                    id: payload.id,
                    result: payload.result,
                });
            }
        }
    };
    worker.postMessage({ cmd: "init", payload: { registry, modelPath } });
}
async function logUncertain(entry) {
    const store = await chrome.storage.local.get(["uncertain"]);
    const list = Array.isArray(store.uncertain) ? store.uncertain : [];
    list.push({ ts: Date.now(), ...entry });
    await chrome.storage.local.set({ uncertain: list });
}
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type === "score-sentences") {
        if (!workerReady || !worker) {
            sendResponse({ ok: false, error: "engine-not-ready" });
            return false;
        }
        const tabId = sender.tab?.id;
        const sentences = Array.isArray(message.sentences)
            ? message.sentences
            : [];
        sentences.forEach((entry, index) => {
            const sentence = typeof entry === "string" ? entry : entry.text;
            const localId = typeof entry === "string" ? `${tabId ?? "tab"}-${index}` : entry.localId ?? `${tabId ?? "tab"}-${index}`;
            worker?.postMessage({
                cmd: "score",
                payload: {
                    id: localId,
                    tabId,
                    sentence,
                },
            });
        });
        sendResponse({ ok: true });
        return true;
    }
    if (message?.type === "export-uncertain") {
        chrome.storage.local.get(["uncertain"]).then((data) => {
            sendResponse({ data: data.uncertain ?? [] });
        });
        return true;
    }
    return false;
});
bootstrap().catch((error) => {
    console.error("Marker engine bootstrap failed", error);
});
export {};
