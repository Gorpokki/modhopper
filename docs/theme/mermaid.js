(async () => {
    const blocks = document.querySelectorAll("code.language-mermaid");
    if (!blocks.length) return;

    const { default: mermaid } = await import("https://cdn.jsdelivr.net/npm/mermaid@11.15.0/dist/mermaid.esm.min.mjs");
    mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: "neutral", flowchart: { useMaxWidth: false } });
    await document.fonts.ready;
    const nodes = Array.from(blocks, (code) => {
        const diagram = code.parentElement;
        diagram.classList.add("mermaid");
        diagram.style.backgroundColor = "white";
        diagram.style.overflowX = "auto";
        diagram.tabIndex = 0;
        diagram.textContent = code.textContent;
        return diagram;
    });
    await mermaid.run({ nodes });
})();
