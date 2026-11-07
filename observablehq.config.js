// Observable Framework 설정 — https://observablehq.com/framework/config
export default {
  title: "부동산 인사이트",
  root: "src",
  output: "dist",
  pages: [
    {name: "네 가지 질문", path: "/"},
    {name: "내 조건으로 보기", path: "/personal"},
    {name: "정책과 의견", path: "/policy"},
    {name: "시장 분석", open: true, pages: [
      {name: "실거래 분석", path: "/trades"},
      {name: "지역 비교", path: "/regions"},
      {name: "10년 추이", path: "/longterm"},
      {name: "시장 지표 (부동산원·KB)", path: "/market"},
      {name: "매수자 분석", path: "/buyers"}
    ]},
    {name: "뉴스·리포트", path: "/news"},
    {name: "내 리포트", path: "/reports/"},
    {name: "도구", open: false, pages: [
      {name: "타겟 단지", path: "/complexes"},
      {name: "예산 계산기", path: "/budget"}
    ]},
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
  footer: "데이터: 국토교통부 실거래가 공개 API · 한국부동산원 R-ONE · KB부동산 · 언론사 RSS(제목·링크만). 투자·법률 자문이 아닙니다.",
  cleanUrls: true
};
