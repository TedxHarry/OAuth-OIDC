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

  const collapseCourseSections = () => {
    document
      .querySelectorAll(
        ".md-sidebar--primary .md-nav__item--nested > .md-nav__toggle"
      )
      .forEach((toggle) => {
        toggle.checked = false;
        toggle.removeAttribute("checked");
      });
  };

  const updateCourseNavButton = (button) => {
    const collapsed =
      document.body.classList.contains("course-nav-collapsed");

    button.textContent = collapsed ? "Course" : "Hide";
    button.setAttribute(
      "aria-label",
      collapsed
        ? "Show course navigation"
        : "Hide course navigation"
    );
    button.setAttribute(
      "aria-expanded",
      collapsed ? "false" : "true"
    );
  };

  const initializeCourseNavToggle = () => {
    let button = document.querySelector(".course-nav-toggle");

    if (!button) {
      button = document.createElement("button");
      button.type = "button";
      button.className = "course-nav-toggle";
      document.body.appendChild(button);

      button.addEventListener("click", () => {
        document.body.classList.toggle("course-nav-collapsed");

        localStorage.setItem(
          "course-nav-collapsed",
          document.body.classList.contains("course-nav-collapsed")
            ? "true"
            : "false"
        );

        updateCourseNavButton(button);
      });
    }

    if (window.innerWidth >= 1220) {
      const saved =
        localStorage.getItem("course-nav-collapsed");

      document.body.classList.toggle(
        "course-nav-collapsed",
        saved === "true"
      );

      button.hidden = false;
      updateCourseNavButton(button);
    } else {
      document.body.classList.remove("course-nav-collapsed");
      button.hidden = true;
    }
  };

  let mermaidModulePromise;

  const getMermaid = async () => {
    if (!mermaidModulePromise) {
      mermaidModulePromise = import(
        "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"
      );
    }

    const module = await mermaidModulePromise;
    return module.default;
  };

  const mermaidThemeCss = `
    .node rect,
    .node polygon,
    .node circle,
    .node ellipse,
    rect.actor {
      fill: #f3e7cf !important;
      stroke: #8c672b !important;
      stroke-width: 1.8px !important;
    }

    text,
    tspan,
    .nodeLabel,
    .nodeLabel *,
    .edgeLabel,
    .edgeLabel *,
    .messageText,
    .labelText,
    .loopText,
    .noteText,
    .actor,
    .cluster-label {
      fill: #172033 !important;
      color: #172033 !important;
      opacity: 1 !important;
      font-weight: 600 !important;
    }

    .edgeLabel rect,
    .labelBox,
    .labelBkg {
      fill: #fffdf8 !important;
      stroke: #c6a564 !important;
      opacity: 1 !important;
    }

    .flowchart-link,
    .messageLine0,
    .messageLine1,
    .actor-line,
    path.path,
    line {
      stroke: #34445a !important;
      stroke-width: 1.9px !important;
      opacity: 1 !important;
    }

    marker path {
      fill: #34445a !important;
      stroke: #34445a !important;
    }

    .note {
      fill: #fff0c7 !important;
      stroke: #9a7130 !important;
    }

    .cluster rect {
      fill: #edf3f1 !important;
      stroke: #497f79 !important;
    }
  `;

  const reinforceMermaidContrast = () => {
    document
      .querySelectorAll(".mermaid svg")
      .forEach((svg) => {
        svg.style.background = "#fffdf8";

        svg
          .querySelectorAll(
            "text, tspan, .nodeLabel, .edgeLabel, .messageText, .labelText, .loopText, .noteText, .cluster-label"
          )
          .forEach((label) => {
            label.style.setProperty(
              "fill",
              "#172033",
              "important"
            );
            label.style.setProperty(
              "color",
              "#172033",
              "important"
            );
            label.style.setProperty(
              "opacity",
              "1",
              "important"
            );
          });

        svg
          .querySelectorAll(
            ".node rect, .node polygon, .node circle, .node ellipse, rect.actor"
          )
          .forEach((shape) => {
            shape.style.setProperty(
              "fill",
              "#f3e7cf",
              "important"
            );
            shape.style.setProperty(
              "stroke",
              "#8c672b",
              "important"
            );
          });
      });
  };

  const initializeMermaid = async () => {
    const nodes = Array.from(
      document.querySelectorAll(".mermaid")
    );

    if (!nodes.length) {
      return;
    }

    try {
      const mermaid = await getMermaid();

      mermaid.initialize({
        startOnLoad: false,
        securityLevel: "strict",
        theme: "base",
        htmlLabels: false,
        flowchart: {
          htmlLabels: false,
          useMaxWidth: true
        },
        themeCSS: mermaidThemeCss,
        themeVariables: {
          background: "#fffdf8",
          primaryColor: "#f3e7cf",
          primaryTextColor: "#172033",
          primaryBorderColor: "#8c672b",
          secondaryColor: "#dcebe8",
          secondaryTextColor: "#172033",
          secondaryBorderColor: "#497f79",
          tertiaryColor: "#edf3f1",
          tertiaryTextColor: "#172033",
          tertiaryBorderColor: "#497f79",
          lineColor: "#34445a",
          textColor: "#172033",
          mainBkg: "#f3e7cf",
          nodeBorder: "#8c672b",
          edgeLabelBackground: "#fffdf8",
          actorBkg: "#f3e7cf",
          actorBorder: "#8c672b",
          actorTextColor: "#172033",
          actorLineColor: "#34445a",
          signalColor: "#34445a",
          signalTextColor: "#172033",
          labelBoxBkgColor: "#fffdf8",
          labelBoxBorderColor: "#c6a564",
          labelTextColor: "#172033",
          loopTextColor: "#172033",
          noteBkgColor: "#fff0c7",
          noteBorderColor: "#9a7130",
          noteTextColor: "#172033",
          activationBkgColor: "#dcebe8",
          activationBorderColor: "#497f79",
          fontFamily:
            "Inter, system-ui, -apple-system, Segoe UI, sans-serif",
          fontSize: "16px"
        }
      });

      nodes.forEach((node) => {
        node.removeAttribute("data-processed");
      });

      await mermaid.run({ nodes });
      reinforceMermaidContrast();
    } catch (error) {
      console.error("Course diagram render failed", error);
    }
  };

  const initializePage = () => {
    initializeCourseNavToggle();
    updateProgress();

    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(
        collapseCourseSections
      );
    });

    initializeMermaid();
  };

  document.addEventListener(
    "scroll",
    updateProgress,
    { passive: true }
  );

  window.addEventListener(
    "resize",
    initializeCourseNavToggle
  );

  if (typeof document$ !== "undefined") {
    document$.subscribe(() => {
      window.requestAnimationFrame(initializePage);
    });
  } else if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      initializePage
    );
  } else {
    initializePage();
  }
})();
