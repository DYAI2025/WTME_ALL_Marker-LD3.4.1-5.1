const SELECTOR = "p,li,blockquote,dd,dt,span,div:not([role]),article,section";
function toSentences(node) {
    const text = node.textContent ?? "";
    return text
        .split(/(?<=[.!?])\s+/)
        .map((part) => part.trim())
        .filter((part) => part.length > 0);
}
function highlight(node, sentence, markerId) {
    const content = node.textContent ?? "";
    const idx = content.indexOf(sentence);
    if (idx < 0)
        return;
    const textNode = node.firstChild;
    if (!textNode || textNode.nodeType !== Node.TEXT_NODE)
        return;
    const range = document.createRange();
    range.setStart(textNode, idx);
    range.setEnd(textNode, idx + sentence.length);
    const mark = document.createElement("mark");
    mark.dataset.markerId = markerId;
    mark.className = "cma-mark";
    mark.title = markerId;
    range.surroundContents(mark);
}
function persist(key, marks) {
    try {
        localStorage.setItem(key, JSON.stringify(marks));
    }
    catch (error) {
        console.warn("persist failed", error);
    }
}
function restore(key) {
    try {
        const raw = localStorage.getItem(key);
        if (!raw)
            return [];
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed : [];
    }
    catch (error) {
        console.warn("restore failed", error);
        return [];
    }
}
(async function main() {
    const blocks = Array.from(document.querySelectorAll(SELECTOR)).filter((el) => el instanceof Element && el.childElementCount === 0 && (el.textContent?.trim().length ?? 0) > 0);
    const items = [];
    blocks.forEach((block, blockIndex) => {
        const sentences = toSentences(block);
        sentences.forEach((sentence, sentenceIndex) => {
            const id = `${blockIndex}:${sentenceIndex}`;
            items.push({ id, blockIndex, sentenceIndex, sentence });
        });
    });
    const payload = items.map((item) => ({ text: item.sentence, localId: item.id }));
    chrome.runtime.sendMessage({ type: "score-sentences", sentences: payload }, () => undefined);
    const state = new Map(items.map((i) => [i.id, i]));
    const highlights = [];
    const storageKey = `cma:${location.href}`;
    const saved = restore(storageKey);
    saved.forEach((mark) => {
        const block = blocks[mark.blockIndex];
        if (block)
            highlight(block, mark.sentence, mark.markerId);
        highlights.push(mark);
    });
    chrome.runtime.onMessage.addListener((message) => {
        if (message?.type !== "marker-result")
            return;
        const { id, result } = message;
        if (!state.has(id))
            return;
        const item = state.get(id);
        if (!result)
            return;
        const sem = Array.isArray(result.semTriggered) ? result.semTriggered : [];
        const clu = Array.isArray(result.cluTriggered) ? result.cluTriggered : [];
        const firstLabel = sem[0] ?? clu[0];
        if (!firstLabel)
            return;
        const block = blocks[item.blockIndex];
        if (!block)
            return;
        highlight(block, item.sentence, firstLabel);
        highlights.push({ blockIndex: item.blockIndex, sentence: item.sentence, markerId: firstLabel });
        persist(storageKey, highlights);
    });
})();
export {};
