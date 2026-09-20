(() => {
  const ensureProgressBar = () => {
    let progress = document.querySelector(".course-progress");

    if (!progress) {
      progress = document.createElement("div");
      progress.className = "course-progress";
      progress.setAttribute("aria-hidden", "true");
      document.body.appendChild(progress);
    }

    return progress;
  };

  const updateProgress = () => {
    const progress = ensureProgressBar();
    const root = document.documentElement;
    const scrollable = root.scrollHeight - root.clientHeight;
    const ratio = scrollable > 0 ? root.scrollTop / scrollable : 0;

    progress.style.width =
      Math.max(0, Math.min(100, ratio * 100)) + "%";
  };

  const collapseCourseNavigation = () => {
    document
      .querySelectorAll(
        ".md-sidebar--primary .md-nav__item--nested > .md-nav__toggle"
      )
      .forEach((toggle) => {
        toggle.checked = false;
        toggle.removeAttribute("checked");
      });
  };

  const initializeMermaid = () => {
    if (!window.mermaid) {
      return;
    }

    const dark =
      document.body.getAttribute("data-md-color-scheme") === "luxury-dark" ||
      (
        window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: dark)").matches
      );

    window.mermaid.initialize({
      startOnLoad: false,
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

    const nodes = document.querySelectorAll(".mermaid");

    if (nodes.length) {
      window.mermaid.run({ nodes });
    }
  };

  const initializePage = () => {
    collapseCourseNavigation();
    updateProgress();
    initializeMermaid();
  };

  document.addEventListener(
    "scroll",
    updateProgress,
    { passive: true }
  );

  window.addEventListener("resize", updateProgress);

  if (typeof document$ !== "undefined") {
    document$.subscribe(() => {
      window.requestAnimationFrame(initializePage);
    });
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializePage);
  } else {
    initializePage();
  }
})();
