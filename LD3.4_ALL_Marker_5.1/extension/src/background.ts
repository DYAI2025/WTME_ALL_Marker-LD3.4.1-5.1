const regUrl = chrome.runtime.getURL("dist/registry.json");
const famUrl = chrome.runtime.getURL("dist/families.json");
let worker: Worker | null = null;

async function init() {
  const modelPath = chrome.runtime.getURL("models");
  const [registry, families] = await Promise.all([
    (await fetch(regUrl)).json(),
    (await fetch(famUrl)).json(),
  ]);
  worker = new Worker(chrome.runtime.getURL("dist/engine.worker.js"), { type: "module" });
  worker.onmessage = (e: MessageEvent) => {
    // passthrough / event routing (hier minimal)
    console.debug("engine:", e.data);
  };
  worker.postMessage({ cmd: "init", payload: { registry, modelPath, families } });
}

init().catch(console.error);


