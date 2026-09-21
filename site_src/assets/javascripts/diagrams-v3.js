(() => {
  let mermaidPromise;

  const palette = {
    ink: "#172033",
    muted: "#475569",
    canvas: "#FBFCFE",
    blue: "#EAF2FF",
    blueBorder: "#3F6FA5",
    green: "#E8F6EE",
    greenBorder: "#3F7D5A",
    amber: "#FFF4D6",
    amberBorder: "#A66A16",
    rose: "#FDECEC",
    roseBorder: "#A54848",
    violet: "#F1EDFF",
    violetBorder: "#6D5EA8"
  };

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
    .actor, .actor text, .actor tspan, foreignObject, foreignObject * {
      fill: ${palette.ink} !important;
      color: ${palette.ink} !important;
      opacity: 1 !important;
      font-weight: 600 !important;
    }

    .flowchart-link, .messageLine0, .messageLine1,
    .actor-line, path.path, line {
      stroke: ${palette.muted} !important;
      stroke-width: 2px !important;
      opacity: 1 !important;
    }

    marker path {
      fill: ${palette.muted} !important;
      stroke: ${palette.muted} !important;
    }

    .edgeLabel rect, .labelBox, .labelBkg {
      fill: #FFFFFF !important;
      stroke: #CBD5E1 !important;
      opacity: 1 !important;
    }

    .note {
      fill: ${palette.amber} !important;
      stroke: ${palette.amberBorder} !important;
    }

    .cluster rect {
      fill: #F3F8F7 !important;
      stroke: #6A8F89 !important;
    }
  `;

  const hasAny = (text, words) => words.some((word) => text.includes(word));

  const classifyNode = (node) => {
    const text = (node.textContent || "").toLowerCase();

    if (node.querySelector("polygon")) {
      return "decision";
    }

    if (
      hasAny(text, [
        "fail", "error", "reject", "denied", "deny", "wrong verifier",
        "no verifier", "no matching", "absent", "invalid", "stolen"
      ])
    ) {
      return "failure";
    }

    if (
      hasAny(text, [
        "passes", "passed", "allowed", "success", "200 ", "200\n",
        "token response", "request allowed", "issued"
      ])
    ) {
      return "success";
    }

    if (
      hasAny(text, [
        "spa", "client", "browser", "learner", "employee", "user",
        "postman", "python", "portal"
      ])
    ) {
      return "client";
    }

    return "default";
  };

  const applySemanticNodeColors = (svg) => {
    svg.querySelectorAll("g.node").forEach((node) => {
      node.classList.remove(
        "diagram-node--default",
        "diagram-node--client",
        "diagram-node--decision",
        "diagram-node--success",
        "diagram-node--failure"
      );
      node.classList.add("diagram-node--" + classifyNode(node));
    });
  };

  const normalizeSvg = (svg) => {
    svg.setAttribute("role", "img");
    svg.setAttribute("focusable", "false");
    svg.style.setProperty("background", "transparent", "important");

    svg.querySelectorAll(
      "text, tspan, .nodeLabel, .nodeLabel *, .edgeLabel, .edgeLabel *, " +
      ".messageText, .labelText, .loopText, .noteText, .cluster-label, " +
      ".actor, .actor text, .actor tspan, foreignObject, foreignObject *"
    ).forEach((el) => {
      el.style.setProperty("fill", palette.ink, "important");
      el.style.setProperty("color", palette.ink, "important");
      el.style.setProperty("opacity", "1", "important");
    });

    svg.querySelectorAll(
      ".flowchart-link, .messageLine0, .messageLine1, .actor-line, path.path, line"
    ).forEach((el) => {
      el.style.setProperty("stroke", palette.muted, "important");
      el.style.setProperty("stroke-width", "2px", "important");
      el.style.setProperty("opacity", "1", "important");
    });

    svg.querySelectorAll("marker path").forEach((el) => {
      el.style.setProperty("fill", palette.muted, "important");
      el.style.setProperty("stroke", palette.muted, "important");
    });

    applySemanticNodeColors(svg);
  };

  const closeExpandedDiagram = () => {
    const expanded = document.querySelector(".diagram-shell.is-expanded");
    if (!expanded) return;

    expanded.classList.remove("is-expanded");
    document.body.classList.remove("diagram-modal-open");

    const button = expanded.querySelector(".diagram-action");
    if (button) {
      button.textContent = "Expand diagram";
      button.setAttribute("aria-expanded", "false");
      button.focus({ preventScroll: true });
    }
  };

  const enhanceDiagram = (node) => {
    if (node.dataset.diagramEnhanced === "true") return;

    const shell = document.createElement("div");
    shell.className = "diagram-shell";

    const actions = document.createElement("div");
    actions.className = "diagram-actions";

    const button = document.createElement("button");
    button.type = "button";
    button.className = "diagram-action";
    button.textContent = "Expand diagram";
    button.setAttribute("aria-expanded", "false");

    node.parentNode.insertBefore(shell, node);
    shell.appendChild(actions);
    actions.appendChild(button);
    shell.appendChild(node);

    button.addEventListener("click", () => {
      const expanded = shell.classList.toggle("is-expanded");
      document.body.classList.toggle("diagram-modal-open", expanded);
      button.textContent = expanded ? "Close diagram" : "Expand diagram";
      button.setAttribute("aria-expanded", expanded ? "true" : "false");
    });

    node.dataset.diagramEnhanced = "true";
  };

  const renderDiagrams = async () => {
    const nodes = Array.from(
      document.querySelectorAll(".mermaid:not([data-processed])")
    );

    if (!nodes.length) {
      document.querySelectorAll(".mermaid").forEach(enhanceDiagram);
      return;
    }

    try {
      const mermaid = await loadMermaid();

      mermaid.initialize({
        startOnLoad: false,
        securityLevel: "strict",
        theme: "base",
        htmlLabels: true,
        flowchart: {
          htmlLabels: true,
          useMaxWidth: false,
          curve: "basis",
          wrappingWidth: 220
        },
        sequence: {
          useMaxWidth: false,
          wrap: true,
          width: 180,
          messageMargin: 42,
          noteMargin: 12
        },
        themeCSS,
        themeVariables: {
          background: palette.canvas,
          primaryColor: palette.blue,
          primaryTextColor: palette.ink,
          primaryBorderColor: palette.blueBorder,
          secondaryColor: palette.green,
          secondaryTextColor: palette.ink,
          secondaryBorderColor: palette.greenBorder,
          tertiaryColor: palette.amber,
          tertiaryTextColor: palette.ink,
          tertiaryBorderColor: palette.amberBorder,
          lineColor: palette.muted,
          textColor: palette.ink,
          mainBkg: palette.blue,
          nodeBorder: palette.blueBorder,
          edgeLabelBackground: "#FFFFFF",
          actorBkg: palette.violet,
          actorBorder: palette.violetBorder,
          actorTextColor: palette.ink,
          actorLineColor: palette.muted,
          signalColor: palette.muted,
          signalTextColor: palette.ink,
          labelBoxBkgColor: "#FFFFFF",
          labelBoxBorderColor: "#CBD5E1",
          labelTextColor: palette.ink,
          loopTextColor: palette.ink,
          noteBkgColor: palette.amber,
          noteBorderColor: palette.amberBorder,
          noteTextColor: palette.ink,
          activationBkgColor: palette.green,
          activationBorderColor: palette.greenBorder,
          fontFamily: "Inter, system-ui, -apple-system, Segoe UI, sans-serif",
          fontSize: "17px"
        }
      });

      await mermaid.run({ nodes });

      nodes.forEach((node) => {
        const svg = node.querySelector("svg");
        if (svg) normalizeSvg(svg);
        enhanceDiagram(node);
      });
    } catch (error) {
      console.error("Diagram rendering failed", error);
    }
  };

  const initialize = () => {
    renderDiagrams();
  };

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeExpandedDiagram();
  });

  if (typeof document$ !== "undefined") {
    document$.subscribe(() => requestAnimationFrame(initialize));
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize);
  } else {
    initialize();
  }
})();
