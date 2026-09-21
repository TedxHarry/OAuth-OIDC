(() => {
  // Rendering model
  // --------------------------------------------------------------------------
  // Material for MkDocs loads the Mermaid library (window.mermaid) but does not
  // auto-render the diagrams in this project, so this script drives the render.
  //
  // Critically, it renders through Material's single window.mermaid instance
  // and never imports a second copy of Mermaid. The previous version imported
  // Mermaid from another CDN and ran it in parallel with Material's instance;
  // the two collided on the same .mermaid nodes and intermittently produced a
  // "Syntax error" box. One instance, one render pass per node, then
  // post-process (semantic node colors, guaranteed dark label text, expand).

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

  const postProcess = () => {
    document.querySelectorAll(".mermaid").forEach((node) => {
      const svg = node.querySelector("svg");
      if (!svg || svg.querySelector(".error-text")) return;

      if (svg.dataset.diagramNormalized !== "true") {
        svg.dataset.diagramNormalized = "true";
        normalizeSvg(svg);
      }
      enhanceDiagram(node);
    });
  };

  const waitForMermaid = (attempts = 80) =>
    new Promise((resolve) => {
      const check = () => {
        if (window.mermaid && typeof window.mermaid.run === "function") {
          resolve(window.mermaid);
        } else if (attempts-- <= 0) {
          resolve(null);
        } else {
          setTimeout(check, 100);
        }
      };
      check();
    });

  // Capture each diagram's source text as early as possible. This script runs
  // during parsing, before Material's async pass converts the <pre class=
  // "mermaid"><code> block into an (often empty) rendered container, so the
  // source is still present here and we stash it to render from later.
  // The build hook wraps every diagram in
  // <div class="diagram-wrap" data-diagram-source="..."> which Material never
  // blanks, so read the source from there first and fall back to the block.
  const captureSources = () => {
    document.querySelectorAll(".mermaid").forEach((node) => {
      if (node.dataset.diagramSource) return;
      const wrap = node.closest(".diagram-wrap");
      const code = node.querySelector("code");
      const source =
        (wrap && wrap.dataset.diagramSource) ||
        (code ? code.textContent : node.textContent) ||
        "";
      if (source.trim()) node.dataset.diagramSource = source;
    });
  };

  let initialized = false;
  let running = false;

  const renderDiagrams = async () => {
    if (running) return;
    captureSources();

    // Nodes we have a source for that are not yet rendered to a diagram.
    const nodes = Array.from(document.querySelectorAll(".mermaid")).filter(
      (node) =>
        node.dataset.diagramRendered !== "true" &&
        !node.querySelector("svg") &&
        (node.dataset.diagramSource || "").trim().length > 0
    );

    if (!nodes.length) {
      postProcess();
      return;
    }

    running = true;
    try {
      const mermaid = await waitForMermaid();
      if (!mermaid) return;

      if (!initialized) {
        initialized = true;
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: "strict",
          theme: "base",
          flowchart: { useMaxWidth: false, curve: "basis", wrappingWidth: 220 },
          sequence: { useMaxWidth: false, wrap: true, width: 180, messageMargin: 42 },
          themeVariables: {
            background: palette.canvas,
            primaryColor: palette.blue,
            primaryTextColor: palette.ink,
            primaryBorderColor: palette.blueBorder,
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
            noteBkgColor: palette.amber,
            noteBorderColor: palette.amberBorder,
            noteTextColor: palette.ink,
            fontFamily: "Inter, system-ui, -apple-system, Segoe UI, sans-serif",
            fontSize: "16px"
          }
        });
      }

      // Claim the nodes and restore their source text (Material may have
      // blanked them), so Mermaid has a valid definition to parse.
      nodes.forEach((node) => {
        node.dataset.diagramRendered = "true";
        node.removeAttribute("data-processed");
        node.textContent = node.dataset.diagramSource;
      });

      await mermaid.run({ nodes });
    } catch (error) {
      console.error("Diagram rendering failed", error);
    } finally {
      running = false;
      postProcess();
    }
  };

  // Drive rendering with setTimeout (works in hidden/background tabs, unlike
  // requestAnimationFrame) and keep retrying until every diagram has rendered.
  // The poll also survives being started before Material has inserted the
  // diagram blocks: it keeps ticking until at least one exists and all are done.
  const boot = () => {
    captureSources();
    let attempts = 80;
    const tick = () => {
      renderDiagrams();
      const total = document.querySelectorAll(".mermaid").length;
      const done = document.querySelectorAll(
        ".mermaid[data-diagram-enhanced]"
      ).length;
      const finished = total > 0 && done >= total;
      if (!finished && attempts-- > 0) setTimeout(tick, 200);
    };
    tick();
  };

  // Grab the source immediately, before Material's render pass can blank it.
  captureSources();

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeExpandedDiagram();
  });

  // Trigger from every available entry point; boot() is idempotent and the
  // poll self-terminates once all diagrams are rendered.
  boot();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  }
  window.addEventListener("load", boot);
  if (typeof document$ !== "undefined") {
    try {
      document$.subscribe(() => boot());
    } catch (error) {
      /* Material not present; lifecycle events already cover rendering. */
    }
  }
})();
