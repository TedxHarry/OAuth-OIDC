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

  const styleRenderedMermaid = () => {
    document.querySelectorAll(".mermaid svg").forEach((svg) => {
      svg.querySelectorAll(
        ".node rect, .node polygon, .node circle, .node ellipse, rect.actor, .actor rect"
      ).forEach((shape) => {
        shape.style.setProperty("fill", "#17263d", "important");
        shape.style.setProperty("stroke", "#b78d49", "important");
        shape.style.setProperty("stroke-width", "1.7px", "important");
      });

      svg.querySelectorAll(
        ".nodeLabel, .nodeLabel p, .nodeLabel span, .node foreignObject div, .actor text, .actor tspan"
      ).forEach((label) => {
        label.style.setProperty("color", "#fffaf0", "important");
        label.style.setProperty("fill", "#fffaf0", "important");
        label.style.setProperty("opacity", "1", "important");
      });

      svg.querySelectorAll(
        ".edgeLabel, .edgeLabel p, .edgeLabel span, .edgeLabel foreignObject div, .messageText, .messageText tspan, .labelText, .labelText tspan, .loopText, .loopText tspan"
      ).forEach((label) => {
        label.style.setProperty("color", "#172033", "important");
        label.style.setProperty("fill", "#172033", "important");
        label.style.setProperty("opacity", "1", "important");
      });

      svg.querySelectorAll(".edgeLabel rect, .labelBox, .labelBkg")
        .forEach((box) => {
          box.style.setProperty("fill", "#fffdf8", "important");
          box.style.setProperty("stroke", "#d1b67e", "important");
          box.style.setProperty("opacity", "1", "important");
        });

      svg.querySelectorAll(
        ".messageLine0, .messageLine1, .actor-line, .flowchart-link, path.path"
      ).forEach((line) => {
        line.style.setProperty("stroke", "#4b5b70", "important");
        line.style.setProperty("stroke-width", "1.8px", "important");
      });

      svg.querySelectorAll("marker path").forEach((marker) => {
        marker.style.setProperty("fill", "#4b5b70", "important");
        marker.style.setProperty("stroke", "#4b5b70", "important");
      });
    });
  };

  const initializeMermaid = async () => {
    if (!window.mermaid) {
      return;
    }

    window.mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      theme: "base",
      themeVariables: {
        background: "#fcfaf5",
        primaryColor: "#17263d",
        primaryTextColor: "#fffaf0",
        primaryBorderColor: "#b78d49",
        secondaryColor: "#204f4b",
        secondaryTextColor: "#fffaf0",
        secondaryBorderColor: "#8fbab5",
        tertiaryColor: "#f2ede2",
        tertiaryTextColor: "#172033",
        tertiaryBorderColor: "#a98a55",
        lineColor: "#4b5b70",
        textColor: "#172033",
        mainBkg: "#17263d",
        nodeBorder: "#b78d49",
        clusterBkg: "#f2ede2",
        clusterBorder: "#a98a55",
        edgeLabelBackground: "#fffdf8",
        actorBkg: "#17263d",
        actorBorder: "#b78d49",
        actorTextColor: "#fffaf0",
        actorLineColor: "#647086",
        signalColor: "#4b5b70",
        signalTextColor: "#172033",
        labelBoxBkgColor: "#fffdf8",
        labelBoxBorderColor: "#d1b67e",
        labelTextColor: "#172033",
        loopTextColor: "#172033",
        noteBkgColor: "#fff1c9",
        noteBorderColor: "#b78d49",
        noteTextColor: "#172033",
        activationBkgColor: "#dcebea",
        activationBorderColor: "#2f6f6a",
        fontFamily: "Inter, system-ui, sans-serif",
        fontSize: "16px"
      }
    });

    document.querySelectorAll(".mermaid").forEach((node) => {
      node.removeAttribute("data-processed");
    });

    const nodes = document.querySelectorAll(".mermaid");

    if (nodes.length) {
      await window.mermaid.run({ nodes });
      styleRenderedMermaid();
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
