(() => {
  const progress = document.createElement("div");
  progress.className = "course-progress";
  progress.setAttribute("aria-hidden", "true");
  document.body.appendChild(progress);

  const updateProgress = () => {
    const root = document.documentElement;
    const scrollable = root.scrollHeight - root.clientHeight;
    const ratio = scrollable > 0 ? root.scrollTop / scrollable : 0;
    progress.style.width = Math.max(0, Math.min(100, ratio * 100)) + "%";
  };

  updateProgress();
  document.addEventListener("scroll", updateProgress, { passive: true });
  window.addEventListener("resize", updateProgress);

  const dark = window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches;

  if (window.mermaid) {
    window.mermaid.initialize({
      startOnLoad: true,
      securityLevel: "strict",
      theme: "base",
      themeVariables: {
        primaryColor: dark ? "#17243a" : "#f7f1e6",
        primaryTextColor: dark ? "#f8f5ef" : "#172033",
        primaryBorderColor: "#b8955a",
        lineColor: dark ? "#aeb8c7" : "#526070",
        secondaryColor: dark ? "#102723" : "#e8f2ef",
        tertiaryColor: dark ? "#161d2a" : "#fffdfa",
        fontFamily: "Inter, system-ui, sans-serif"
      }
    });
  }
})();
