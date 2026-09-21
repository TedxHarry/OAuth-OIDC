(() => {
  // Material for MkDocs already loads Mermaid and renders every ```mermaid```
  // block exactly once. This script must NOT render Mermaid a second time:
  // doing so re-parses the already-rendered <svg> as diagram source and
  // replaces it with a "Syntax error" box. Instead we wait for Material's
  // rendered SVG and only post-process it (semantic node colors, guaranteed
  // dark label text, and the expand-to-read control).

  const palette = {
    ink: "#172033",
    muted: "#475569"
  };

  const hasAny = (text, words) => words.some((word) => text.includes(word));

  const classifyNode = (node) => {
    const text = (node.textContent || "").toLowerCase();

    if (node.querySelector("polygon") || node.querySelector(".label-container[rx='0']")) {
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

  // Post-process every diagram Material has finished rendering. Returns true
  // once all diagrams on the page are rendered and enhanced.
  const processDiagrams = () => {
    const nodes = Array.from(document.querySelectorAll(".mermaid"));
    let allReady = nodes.length > 0;

    nodes.forEach((node) => {
      if (node.dataset.diagramEnhanced === "true") return;

      const svg = node.querySelector("svg");
      // Wait until Material has injected a real diagram (not still empty and
      // not a Mermaid error placeholder).
      if (!svg || svg.querySelector(".error-text")) {
        allReady = false;
        return;
      }

      normalizeSvg(svg);
      enhanceDiagram(node);
    });

    return allReady;
  };

  // Material renders asynchronously, so poll briefly until each diagram exists.
  const pump = (attempts) => {
    if (processDiagrams()) return;
    if (attempts <= 0) return;
    setTimeout(() => pump(attempts - 1), 150);
  };

  const initialize = () => pump(40);

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
