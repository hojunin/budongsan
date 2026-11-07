import * as echarts from "npm:echarts@6.1.0";
import {PALETTE} from "./ui.js";

export function chart(option, invalidation) {
  const node = document.createElement("div");
  node.className = "interactive-chart";
  node.setAttribute("role", "img");
  node.setAttribute("aria-label", option.series.map((s) => s.name).filter(Boolean).join(" · "));
  let instance;
  const theme = matchMedia("(prefers-color-scheme: dark)");
  const motion = matchMedia("(prefers-reduced-motion: reduce)");
  function render() {
    if (!instance) return;
    const style = getComputedStyle(document.documentElement);
    const muted = style.getPropertyValue("--theme-foreground-muted").trim();
    const border = style.getPropertyValue("--color-lightGrey").trim();
    const axes = (axis) => ({
      type: "value", nameTextStyle: {color: muted, fontSize: 10},
      splitLine: {lineStyle: {color: border, type: "dashed"}}, ...axis,
      axisLabel: {color: muted, fontSize: 10, hideOverlap: true, ...axis.axisLabel}
    });
    const {legend, tooltip, ...settings} = option;
    const yAxis = [option.yAxis ?? {}].flat().map(axes);
    instance.setOption({
      color: PALETTE, animation: !motion.matches, animationDuration: 300,
      textStyle: {fontFamily: style.getPropertyValue("--sans-serif").trim(), color: muted},
      aria: {enabled: true},
      legend: {type: "scroll", top: 0, left: 0, right: 0, textStyle: {color: muted, fontSize: 11}, itemWidth: 14, itemHeight: 7, pageTextStyle: {color: muted}, ...legend},
      tooltip: {trigger: "axis", confine: true, renderMode: "richText", backgroundColor: style.getPropertyValue("--theme-background-alt").trim(), textStyle: {color: muted, fontSize: 12}, axisPointer: {type: "cross"}, ...tooltip},
      toolbox: {top: 28, right: 0, itemSize: 14, iconStyle: {borderColor: muted}, feature: {restore: {title: "초기화"}, saveAsImage: {title: "이미지 저장", pixelRatio: 2}}},
      grid: {left: 8, right: 12, top: 84, bottom: 72, containLabel: true},
      dataZoom: [{type: "slider", height: 20, bottom: 8, borderColor: border, textStyle: {color: muted, fontSize: 10}}, {type: "inside", zoomOnMouseWheel: "ctrl", moveOnMouseMove: false}],
      ...settings,
      graphic: option.series.some((s) => s.data?.length) ? [] : [{type: "text", left: "center", top: "middle", style: {text: "조건에 맞는 데이터가 없습니다", fill: muted, fontSize: 12}}],
      xAxis: axes({type: "category", boundaryGap: false, ...option.xAxis, splitLine: {show: false}}),
      yAxis,
      series: option.series.map((s) => ({showSymbol: false, symbolSize: 5, connectNulls: false, lineStyle: {width: 2}, emphasis: {focus: "series"}, ...s}))
    }, {notMerge: true});
  }
  const observer = new ResizeObserver(([entry]) => {
    if (!entry.contentRect.width) return;
    if (!instance) { instance = echarts.init(node, null, {renderer: "svg"}); render(); }
    else instance.resize();
  });
  observer.observe(node);
  theme.addEventListener("change", render);
  motion.addEventListener("change", render);
  invalidation.then(() => {
    observer.disconnect();
    theme.removeEventListener("change", render);
    motion.removeEventListener("change", render);
    instance?.dispose();
    instance = null;
  });
  return node;
}
