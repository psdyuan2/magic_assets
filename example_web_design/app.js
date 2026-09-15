(() => {
  const tabs = [...document.querySelectorAll("[data-tab]")];
  const form = document.getElementById("collar-form");
  const nameInput = document.getElementById("collar-name");
  const collar = document.querySelector(".collar");
  const collarName = document.querySelector(".collar-name");
  const colorLabel = document.querySelector(".plate-color");
  const claspLabel = document.querySelector(".plate-clasp");
  const note = document.getElementById("order-note");

  const colors = {
    sesame: "芝麻皮",
    persimmon: "柿子皮",
    ink: "墨色皮",
    moss: "苔绿皮",
  };
  const clasps = {
    bone: "骨头扣",
    metal: "铜环",
    wood: "木栓",
  };

  function setCurrent(id) {
    for (const tab of tabs) {
      tab.classList.toggle("is-current", tab.dataset.tab === id);
    }
  }

  function syncPlate() {
    const color = form.elements.color.value;
    const clasp = form.elements.clasp.value;
    const name = (nameInput.value.trim() || "芝麻").slice(0, 6);
    collar.dataset.color = color;
    collarName.textContent = name;
    colorLabel.textContent = colors[color];
    claspLabel.textContent = clasps[clasp];
  }

  for (const tab of tabs) {
    tab.addEventListener("click", () => setCurrent(tab.dataset.tab));
  }

  const observer = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (visible?.target.id) setCurrent(visible.target.id === "walk" ? "walk" : visible.target.id);
  }, { rootMargin: "-20% 0px -55% 0px", threshold: [0.2, 0.5] });

  for (const id of ["shop", "shelf", "walk", "bench"]) {
    const node = document.getElementById(id);
    if (node) observer.observe(node);
  }

  form.addEventListener("input", syncPlate);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    syncPlate();
    note.hidden = false;
    window.clearTimeout(note._hide);
    note._hide = window.setTimeout(() => {
      note.hidden = true;
    }, 2400);
  });
})();
