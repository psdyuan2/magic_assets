(() => {
  const TRIGGERS = new Set(["loop", "mount", "click", "hover", "inview"]);

  function fxName(el) {
    return (el.getAttribute("data-ma-fx") || "").trim();
  }

  function triggerOf(el) {
    const value = (el.getAttribute("data-ma-trigger") || "").trim();
    return TRIGGERS.has(value) ? value : "";
  }

  function applyName(el) {
    const name = fxName(el);
    if (!name) return;
    el.classList.add("ma-fx");
    for (const cls of [...el.classList]) {
      if (cls.startsWith("ma-fx--")) el.classList.remove(cls);
    }
    el.classList.add(`ma-fx--${name}`);
  }

  function play(el) {
    const loop = el.classList.contains("ma-fx-loop");
    el.classList.remove("is-playing");
    if (loop) el.classList.remove("ma-fx-loop");
    void el.offsetWidth;
    if (loop) el.classList.add("ma-fx-loop");
    el.classList.add("is-playing");
  }

  function stop(el) {
    el.classList.remove("is-playing");
    el.classList.remove("ma-fx-loop");
  }

  function bindOne(el) {
    if (el.dataset.maBound === "1") return;
    el.dataset.maBound = "1";
    applyName(el);
    const trigger = triggerOf(el);
    if (trigger === "loop") {
      el.classList.add("ma-fx-loop");
      return;
    }
    if (trigger === "mount") {
      play(el);
      return;
    }
    if (trigger === "click") {
      el.addEventListener("click", () => play(el));
      return;
    }
    if (trigger === "hover") {
      el.addEventListener("pointerenter", () => play(el));
      return;
    }
    if (trigger === "inview" && "IntersectionObserver" in window) {
      const observer = new IntersectionObserver((entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            play(el);
            observer.unobserve(el);
          }
        }
      }, { threshold: 0.4 });
      observer.observe(el);
    }
  }

  function bind(root = document) {
    root.querySelectorAll("[data-ma-fx]").forEach(bindOne);
  }

  const api = { bind, play, stop, applyName };
  if (typeof window !== "undefined") {
    window.MagicFx = api;
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", () => bind(document));
    } else {
      bind(document);
    }
  }
  if (typeof module === "object" && module.exports) module.exports = api;
})();
