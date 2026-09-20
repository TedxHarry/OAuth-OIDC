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

  const mermaidSvgs = () => {
    return Array.from(
      document.querySelectorAll(
        ".mermaid svg, svg[id^='mermaid-'], svg[aria-roledescription*='flowchart'], svg[aria-roledescription*='sequence']"
      )
    );
  };

  const styleRenderedMermaid = () => {
    mermaidSvgs().forEach((svg) => {
      svg.style.setProperty("background", "#fffdf8", "important");

      svg.querySelectorAll(
        "text, tspan, foreignObject, foreignObject *, .nodeLabel, .nodeLabel *, .edgeLabel, .edgeLabel *, .messageText, .messageText *, .labelText, .labelText *, .loopText, .loopText *, .noteText, .noteText *, .cluster-label, .cluster-label *"
      ).forEach((label) => {
        label.style.setProperty("color", "#172033", "important");
        label.style.setProperty("fill", "#172033", "important");
        label.style.setProperty("opacity", "1", "important");
      });

      svg.querySelectorAll(
        ".node rect, .node polygon, .node circle, .node ellipse, rect.actor, .actor rect"
      ).forEach((shape) => {
        shape.setAttribute("fill", "#f3e7cf");
        shape.setAttribute("stroke", "#8c672b");
        shape.style.setProperty("fill", "#f3e7cf", "important");
        shape.style.setProperty("stroke", "#8c672b", "important");
        shape.style.setProperty("stroke-width", "1.8px", "important");
        shape.style.setProperty("opacity", "1", "important");
      });

      svg.querySelectorAll(".edgeLabel rect, .labelBox, .labelBkg")
        .forEach((box) => {
          box.setAttribute("fill", "#fffdf8");
          box.style.setProperty("fill", "#fffdf8", "important");
          box.style.setProperty("stroke", "#c6a564", "important");
          box.style.setProperty("opacity", "1", "important");
        });

      svg.querySelectorAll(
        ".messageLine0, .messageLine1, .actor-line, .flowchart-link, path.path, line"
      ).forEach((line) => {
        line.setAttribute("stroke", "#34445a");
        line.style.setProperty("stroke", "#34445a", "important");
        line.style.setProperty("stroke-width", "1.9px", "important");
        line.style.setProperty("opacity", "1", "important");
      });

      svg.querySelectorAll("marker path").forEach((marker) => {
        marker.setAttribute("fill", "#34445a");
        marker.setAttribute("stroke", "#34445a");
        marker.style.setProperty("fill", "#34445a", "important");
        marker.style.setProperty("stroke", "#34445a", "important");
      });
    });
  };

  let mermaidObserver;

  const observeMermaidRendering = () => {
    if (mermaidObserver) {
      mermaidObserver.disconnect();
    }

    mermaidObserver = new MutationObserver(() => {
      styleRenderedMermaid();
    });

    mermaidObserver.observe(document.body, {
      childList: true,
      subtree: true
    });

    window.setTimeout(styleRenderedMermaid, 50);
    window.setTimeout(styleRenderedMermaid, 250);
    window.setTimeout(styleRenderedMermaid, 750);
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
        primaryColor: "#f3e7cf",
        primaryTextColor: "#172033",
        primaryBorderColor: "#8c672b",
        secondaryColor: "#dcebe8",
        secondaryTextColor: "#172033",
        secondaryBorderColor: "#497f79",
        tertiaryColor: "#f2ede2",
        tertiaryTextColor: "#172033",
        tertiaryBorderColor: "#a98a55",
        lineColor: "#4b5b70",
        textColor: "#172033",
        mainBkg: "#f3e7cf",
        nodeBorder: "#8c672b",
        clusterBkg: "#f2ede2",
        clusterBorder: "#a98a55",
        edgeLabelBackground: "#fffdf8",
        actorBkg: "#f3e7cf",
        actorBorder: "#8c672b",
        actorTextColor: "#172033",
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
      observeMermaidRendering();
    }
  };

  const initializePage = () => {
    initializeCourseNavToggle();
    updateProgress();
    initializeMermaid();
    observeMermaidRendering();

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
