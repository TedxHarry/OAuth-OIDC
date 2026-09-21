(() => {
  let mermaidPromise;

  const loadMermaid = async () => {
    if (!mermaidPromise) {
      mermaidPromise = import(
        "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"
      );
    }
    const module = await mermaidPromise;
    return module.default;
  };

  const themeCSS = `
    text, tspan, .nodeLabel, .nodeLabel *, .edgeLabel, .edgeLabel *,
    .messageText, .labelText, .loopText, .noteText, .cluster-label,
    .actor, .actor text, .actor tspan {
      fill: #111827 !important;
      color: #111827 !important;
      opacity: 1 !important;
      font-weight: 600 !important;
    }

    .node rect, .node polygon, .node circle, .node ellipse,
    rect.actor, .actor rect {
      fill: #F6E8C8 !important;
      stroke: #8A6428 !important;
      stroke-width: 2px !important;
      opacity: 1 !important;
    }

    .edgeLabel rect, .labelBox, .labelBkg {
      fill: #FFFDF8 !important;
      stroke: #C7A766 !important;
      opacity: 1 !important;
    }

    .flowchart-link, .messageLine0, .messageLine1,
    .actor-line, path.path, line {
      stroke: #334155 !important;
      stroke-width: 2px !important;
      opacity: 1 !important;
    }

    marker path {
      fill: #334155 !important;
      stroke: #334155 !important;
    }

    .note {
      fill: #FFF1C7 !important;
      stroke: #8A6428 !important;
    }

    .cluster rect {
      fill: #EAF2EF !important;
      stroke: #2F6F6A !important;
    }
  `;

  const forceContrast = (svg) => {
    svg.style.setProperty("background", "#FFFDF8", "important");

    svg.querySelectorAll(
      "text, tspan, .nodeLabel, .nodeLabel *, .edgeLabel, .edgeLabel *, " +
      ".messageText, .labelText, .loopText, .noteText, .cluster-label, " +
      ".actor, .actor text, .actor tspan, foreignObject, foreignObject *"
    ).forEach((el) => {
      el.style.setProperty("fill", "#111827", "important");
      el.style.setProperty("color", "#111827", "important");
      el.style.setProperty("opacity", "1", "important");
    });

    svg.querySelectorAll(
      ".node rect, .node polygon, .node circle, .node ellipse, rect.actor, .actor rect"
    ).forEach((el) => {
      el.style.setProperty("fill", "#F6E8C8", "important");
      el.style.setProperty("stroke", "#8A6428", "important");
      el.style.setProperty("stroke-width", "2px", "important");
      el.style.setProperty("opacity", "1", "important");
    });

    svg.querySelectorAll(".edgeLabel rect, .labelBox, .labelBkg").forEach((el) => {
      el.style.setProperty("fill", "#FFFDF8", "important");
      el.style.setProperty("stroke", "#C7A766", "important");
      el.style.setProperty("opacity", "1", "important");
    });

    svg.querySelectorAll(
      ".flowchart-link, .messageLine0, .messageLine1, .actor-line, path.path, line"
    ).forEach((el) => {
      el.style.setProperty("stroke", "#334155", "important");
      el.style.setProperty("stroke-width", "2px", "important");
      el.style.setProperty("opacity", "1", "important");
    });

    svg.querySelectorAll("marker path").forEach((el) => {
      el.style.setProperty("fill", "#334155", "important");
      el.style.setProperty("stroke", "#334155", "important");
    });
  };

  const renderDiagrams = async () => {
    const nodes = Array.from(document.querySelectorAll(".mermaid"));
    if (!nodes.length) return;

    try {
      const mermaid = await loadMermaid();

      mermaid.initialize({
        startOnLoad: false,
        securityLevel: "strict",
        theme: "base",
        htmlLabels: false,
        flowchart: {
          htmlLabels: false,
          useMaxWidth: true,
          curve: "basis"
        },
        sequence: {
          useMaxWidth: true,
          wrap: true
        },
        themeCSS,
        themeVariables: {
          background: "#FFFDF8",
          primaryColor: "#F6E8C8",
          primaryTextColor: "#111827",
          primaryBorderColor: "#8A6428",
          secondaryColor: "#DDEDE9",
          secondaryTextColor: "#111827",
          secondaryBorderColor: "#2F6F6A",
          tertiaryColor: "#EAF2EF",
          tertiaryTextColor: "#111827",
          tertiaryBorderColor: "#2F6F6A",
          lineColor: "#334155",
          textColor: "#111827",
          mainBkg: "#F6E8C8",
          nodeBorder: "#8A6428",
          edgeLabelBackground: "#FFFDF8",
          actorBkg: "#F6E8C8",
          actorBorder: "#8A6428",
          actorTextColor: "#111827",
          actorLineColor: "#475569",
          signalColor: "#334155",
          signalTextColor: "#111827",
          labelBoxBkgColor: "#FFFDF8",
          labelBoxBorderColor: "#C7A766",
          labelTextColor: "#111827",
          loopTextColor: "#111827",
          noteBkgColor: "#FFF1C7",
          noteBorderColor: "#8A6428",
          noteTextColor: "#111827",
          activationBkgColor: "#DDEDE9",
          activationBorderColor: "#2F6F6A",
          fontFamily: "Inter, system-ui, -apple-system, Segoe UI, sans-serif",
          fontSize: "17px"
        }
      });

      nodes.forEach((node) => node.removeAttribute("data-processed"));
      await mermaid.run({ nodes });

      document.querySelectorAll(".mermaid svg").forEach(forceContrast);

      setTimeout(() => {
        document.querySelectorAll(".mermaid svg").forEach(forceContrast);
      }, 100);
    } catch (error) {
      console.error("Diagram rendering failed", error);
    }
  };

  const initialize = () => {
    renderDiagrams();
  };

  if (typeof document$ !== "undefined") {
    document$.subscribe(() => requestAnimationFrame(initialize));
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize);
  } else {
    initialize();
  }
})();
