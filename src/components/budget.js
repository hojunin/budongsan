// 예산·대출 계산 (문서 ①탭의 가정과 같은 식). 단위: 만 원.

// 30년 원리금균등 월 상환액
export function monthlyPayment(loan, ratePct, years = 30) {
  const r = ratePct / 100 / 12, n = years * 12;
  return r === 0 ? loan / n : (loan * r) / -Math.expm1(-n * Math.log1p(r));
}

// DSR 40% 기준 최대 대출액 (스트레스 금리 반영)
export function dsrLimit(income, ratePct, stressPct = 0, years = 30, dsr = 0.4) {
  const annual = monthlyPayment(1, ratePct + stressPct, years) * 12;
  return (income * dsr) / annual;
}

// 1주택 취득세 + 지방교육세 (전용 85㎡ 이하), 생애최초 감면 200만 원
export function acquisitionTax(price, firstHome = true) {
  const eok = price / 10000;
  let rate;
  if (eok <= 6) rate = 0.01;
  else if (eok <= 9) rate = (eok * 2 / 3 - 3) / 100;
  else rate = 0.03;
  const tax = price * rate * 1.1;
  return Math.max(0, tax - (firstHome ? 200 : 0));
}

// 스트레스 금리 적용 비율 (수도권 하한 3%)
export const STRESS = {"변동": 1.0, "5년 혼합형": 0.8, "5년 주기형": 0.4, "순수 고정": 0};

export function scenario({price, cash, income, rate, product, stressBase = 3}) {
  const ltvCap = product === "디딤돌" ? Math.min(price * 0.7, 32000) : Math.min(price * 0.7, 60000);
  const stress = product === "디딤돌" ? 0 : stressBase * (STRESS[product] ?? 1);
  // 디딤돌은 DTI 60% 심사 (근사: 연 원리금 ≤ 소득 × 60%)
  const incomeCap = product === "디딤돌"
    ? (income * 0.6) / (monthlyPayment(1, rate) * 12)
    : dsrLimit(income, rate, stress);
  const loan = Math.max(0, Math.min(ltvCap, incomeCap, price));
  const tax = acquisitionTax(price);
  const need = price - loan + tax;
  const eligibleA = product !== "디딤돌" || price <= 60000;
  return {loan, tax, need, gap: cash - need, monthly: monthlyPayment(loan, rate), eligibleA, ltvCap, incomeCap};
}
