// Observable Framework 설정 — https://observablehq.com/framework/config
export default {
  title: "첫 집 데이터",
  root: "src",
  output: "dist",
  pages: [
    {name: "시장 한눈에", path: "/"},
    {name: "지역 비교", path: "/regions"},
    {name: "타겟 단지", path: "/complexes"},
    {name: "시장 온도 (KB)", path: "/market"},
    {name: "예산 계산기", path: "/budget"},
    {name: "데이터 사전", path: "/about"}
  ],
  // 테마(air/near-midnight)와 토큰은 style.css 에서 불러온다. 라이트/다크 자동.
  style: "style.css",
  head: `
<meta name="theme-color" content="#f7f6f3" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#14161a" media="(prefers-color-scheme: dark)">
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='%23c8553d'/><path d='M8 22V13l8-6 8 6v9h-5v-6h-6v6z' fill='white'/></svg>">`,
  sidebar: true,
  toc: false,
  pager: false,
  search: false,
  footer: "데이터: 국토교통부 실거래가 공개 API · KB부동산 데이터허브. 투자·법률 자문이 아닙니다.",
  cleanUrls: true
};
