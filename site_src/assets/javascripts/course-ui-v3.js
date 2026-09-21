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
    progress.style.width = Math.max(0, Math.min(100, ratio * 100)) + "%";
  };

  const organizeCourseSections = () => {
    document
      .querySelectorAll(".md-sidebar--primary .md-nav__item--nested > .md-nav__toggle")
      .forEach((toggle) => {
        const item = toggle.closest(".md-nav__item--nested");
        if (!item) return;

        const active =
          item.classList.contains("md-nav__item--active") ||
          Boolean(item.querySelector(".md-nav__link--active"));

        toggle.checked = active;

        if (active) {
          toggle.setAttribute("checked", "");
        } else {
          toggle.removeAttribute("checked");
        }
      });
  };

  const updateToggle = (button) => {
    const collapsed = document.body.classList.contains("course-nav-collapsed");

    button.setAttribute(
      "aria-label",
      collapsed ? "Show course navigation" : "Hide course navigation"
    );
    button.setAttribute("aria-expanded", collapsed ? "false" : "true");
    button.title = collapsed ? "Show course navigation" : "Hide course navigation";
  };

  const initializeCourseNav = () => {
    let button = document.querySelector(".course-nav-toggle-v3");

    if (!button) {
      button = document.createElement("button");
      button.type = "button";
      button.className = "course-nav-toggle-v3";
      button.innerHTML = "<span aria-hidden='true'>☰</span>";
      document.body.appendChild(button);

      button.addEventListener("click", () => {
        document.body.classList.toggle("course-nav-collapsed");
        localStorage.setItem(
          "course-nav-collapsed",
          document.body.classList.contains("course-nav-collapsed")
            ? "true"
            : "false"
        );
        updateToggle(button);
      });
    }

    if (window.innerWidth >= 1220) {
      const saved = localStorage.getItem("course-nav-collapsed");
      document.body.classList.toggle("course-nav-collapsed", saved === "true");
      button.hidden = false;
      updateToggle(button);
    } else {
      document.body.classList.remove("course-nav-collapsed");
      button.hidden = true;
    }
  };

  const initializePage = () => {
    initializeCourseNav();
    updateProgress();

    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(organizeCourseSections);
    });
  };

  document.addEventListener("scroll", updateProgress, { passive: true });
  window.addEventListener("resize", initializeCourseNav);

  if (typeof document$ !== "undefined") {
    document$.subscribe(() => window.requestAnimationFrame(initializePage));
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializePage);
  } else {
    initializePage();
  }
})();
