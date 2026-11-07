import TomSelect from "npm:tom-select@2.6.2";
import {animate} from "npm:motion@14.9.0/mini";

// Enhance replacement inputs and card containers, keeping chart marks untouched.
export function enhanceUI(invalidation, root = document.querySelector("#observablehq-main")) {
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const seen = new WeakSet();
  const active = new Set();
  const selects = new Map();
  let infoTimer;
  const closeInfo = (except) => root.querySelectorAll(".chart-info[open]").forEach((info) => { if (info !== except) info.open = false; });
  function enterInfo(event) {
    const info = event.target.closest(".chart-info");
    if (event.pointerType !== "mouse" || !info) return;
    clearTimeout(infoTimer);
    closeInfo(info);
    info.open = true;
  }
  function leaveInfo(event) {
    const info = event.target.closest(".chart-info");
    if (event.pointerType !== "mouse" || !info || info.contains(event.relatedTarget)) return;
    infoTimer = setTimeout(() => { info.open = false; }, 120);
  }
  function dismissInfo(event) {
    if (event.type === "keydown" ? event.key === "Escape" : !event.target.closest(".chart-info")) closeInfo();
  }
  function focusInfo(event) {
    const info = event.target.closest(".chart-info");
    if (info && event.target.matches("summary:focus-visible")) { closeInfo(info); info.open = true; }
  }
  function blurInfo(event) {
    const info = event.target.closest(".chart-info");
    if (info && !info.contains(event.relatedTarget)) info.open = false;
  }
  function toggleInfo(event) {
    if (event.target.matches(".chart-info[open]")) closeInfo(event.target);
  }
  root.addEventListener("pointerover", enterInfo);
  root.addEventListener("pointerout", leaveInfo);
  root.addEventListener("focusin", focusInfo);
  root.addEventListener("focusout", blurInfo);
  root.addEventListener("toggle", toggleInfo, true);
  document.addEventListener("pointerdown", dismissInfo);
  document.addEventListener("keydown", dismissInfo);

  function reveal() {
    for (const [select, control] of selects) {
      if (!root.contains(select)) { control.destroy(); selects.delete(select); }
    }
    for (const select of root.querySelectorAll(".filters select")) {
      if (selects.has(select)) continue;
      const control = new TomSelect(select, {
        plugins: select.multiple ? {remove_button: {title: "제거"}} : {},
        maxItems: select.multiple ? select.size || null : 1,
        placeholder: "검색해서 선택…", maxOptions: 100,
        render: {no_results: () => '<div class="no-results">검색 결과가 없습니다</div>'}
      });
      if (select.multiple) {
        // Only transforms change when chips are removed; their layout origins stay fixed.
        const positionItems = () => {
          let x = 0;
          for (const node of control.control.querySelectorAll(".item, input")) {
            node.style.transform = `translateX(${x}px)`;
            x += node.getBoundingClientRect().width + 4;
          }
        };
        control.on("item_add item_remove clear", positionItems);
        control.hook("after", "setCaret", positionItems);
        positionItems();
        document.fonts.ready.then(() => { if (select.isConnected) positionItems(); });
      }
      selects.set(select, control);
    }
    const fresh = [...root.querySelectorAll(".card, .interactive-chart")].filter((node) => !seen.has(node));
    fresh.forEach((node, i) => {
      seen.add(node);
      if (reduced.matches) return;
      const animation = animate(node, {opacity: [0.45, 1], transform: ["translateY(8px)", "translateY(0px)"]}, {duration: .28, delay: Math.min(i, 3) * .04});
      active.add(animation);
      animation.finished.then(() => active.delete(animation));
    });
  }
  function stop() {
    active.forEach((animation) => animation.cancel());
    active.clear();
  }
  function onPreference() { if (reduced.matches) stop(); }
  const observer = new MutationObserver(reveal);
  observer.observe(root, {childList: true, subtree: true});
  reduced.addEventListener("change", onPreference);
  reveal();
  const dispose = () => {
    clearTimeout(infoTimer);
    root.removeEventListener("pointerover", enterInfo);
    root.removeEventListener("pointerout", leaveInfo);
    root.removeEventListener("focusin", focusInfo);
    root.removeEventListener("focusout", blurInfo);
    root.removeEventListener("toggle", toggleInfo, true);
    document.removeEventListener("pointerdown", dismissInfo);
    document.removeEventListener("keydown", dismissInfo);
    observer.disconnect();
    selects.forEach((control) => control.destroy());
    selects.clear();
    reduced.removeEventListener("change", onPreference);
    stop();
  };
  invalidation.then(dispose);
  return dispose;
}
