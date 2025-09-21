const output = document.getElementById("out");
const button = document.getElementById("export");
function asPrettified(data) {
    return JSON.stringify(data, null, 2);
}
button?.addEventListener("click", () => {
    chrome.runtime.sendMessage({ type: "export-uncertain" }, (response) => {
        const items = response?.data ?? [];
        if (!Array.isArray(items)) {
            if (output)
                output.textContent = "Keine Daten";
            return;
        }
        const blob = new Blob([asPrettified(items)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = "uncertain.json";
        anchor.click();
        URL.revokeObjectURL(url);
        if (output)
            output.textContent = `exportiert: ${items.length}`;
    });
});
export {};
