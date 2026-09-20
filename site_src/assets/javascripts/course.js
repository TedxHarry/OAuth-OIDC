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

    button.textContent = collapsed ? "☰ Course" : "‹ Hide course";
    button.setAttribute(
      "aria-label",
      collapsed
        ? "Show course navigation"
        : "Hide course navigation"
    );
    button.setAttribute("aria-expanded", collapsed ? "false" : "true");
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
      const saved = localStorage.getItem("course-nav-collapsed");

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

  const initializeMermaid = () => {
    if (!window.mermaid) {
      return;
    }

    window.mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      theme: "base",
      themeVariables: {
        background: "#fbf8f1",
        primaryColor: "#f4ead8",
        primaryTextColor: "#172033",
        primaryBorderColor: "#9b753a",
        secondaryColor: "#e8f2ef",
        secondaryTextColor: "#172033",
        secondaryBorderColor: "#2f6f6a",
        tertiaryColor: "#edf1f7",
        tertiaryTextColor: "#172033",
        tertiaryBorderColor: "#52627a",
        lineColor: "#465568",
        textColor: "#172033",
        mainBkg: "#f4ead8",
        nodeBorder: "#9b753a",
        clusterBkg: "#fffdf8",
        clusterBorder: "#c8a76e",
        edgeLabelBackground: "#fffdf8",
        actorBkg: "#f4ead8",
        actorBorder: "#9b753a",
        actorTextColor: "#172033",
        actorLineColor: "#687386",
        signalColor: "#334155",
        signalTextColor: "#172033",
        labelBoxBkgColor: "#fffdf8",
        labelBoxBorderColor: "#c8a76e",
        labelTextColor: "#172033",
        loopTextColor: "#172033",
        noteBkgColor: "#fff0c7",
        noteBorderColor: "#b8955a",
        noteTextColor: "#172033",
        activationBkgColor: "#dcebea",
        activationBorderColor: "#2f6f6a",
        fontFamily: "Inter, system-ui, sans-serif",
        fontSize: "16px"
      },
      themeCSS: `
        .actor, .node rect, .node polygon, .node circle {
          stroke-width: 1.5px !important;
        }

        .messageLine0,
        .messageLine1,
        .actor-line,
        .flowchart-link {
          stroke: #465568 !important;
          stroke-width: 1.6px !important;
        }

        marker path {
          fill: #465568 !important;
          stroke: #465568 !important;
        }

        .messageText,
        .labelText,
        .loopText,
        .noteText,
        .nodeLabel,
        .edgeLabel,
        .actor text,
        text {
          fill: #172033 !important;
          color: #172033 !important;
        }

        .labelBox,
        .edgeLabel rect {
          fill: #fffdf8 !important;
          stroke: #c8a76e !important;
        }
      `
    });

    document.querySelectorAll(".mermaid").forEach((node) => {
      node.removeAttribute("data-processed");
    });

    const nodes = document.querySelectorAll(".mermaid");

    if (nodes.length) {
      window.mermaid.run({ nodes });
    }
  };

  const initializePage = () => {
    initializeCourseNavToggle();
    updateProgress();
    initializeMermaid();

    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(collapseCourseSections);
    });
  };

  document.addEventListener(
    "scroll",
    updateProgress,
    { passive: true }
  );

  window.addEventListener("resize", initializeCourseNavToggle);

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
