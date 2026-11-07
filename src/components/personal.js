import {monthlyPayment} from "./budget.js";

// 모든 금액은 만원, 금리는 연 %다.
export function personalScenario(v) {
  const keys = ["price", "cash", "income", "living", "debt", "housing", "loan", "rate", "years", "cost", "reserve"];
  if (keys.some((k) => v[k] === "" || v[k] == null || !Number.isFinite(Number(v[k])) || Number(v[k]) < 0)) return null;
  const x = Object.fromEntries(keys.map((k) => [k, Number(v[k])]));
  if (!Number.isInteger(x.years) || x.years < 1 || x.years > 50 || x.loan > x.price || x.rate > 100) return null;
  const payment = (rate) => monthlyPayment(x.loan, rate, x.years);
  const cash = x.cash - (x.price - x.loan) - x.cost;
  const remaining = (rate) => x.income - x.living - x.debt - x.housing - payment(rate);
  return {cash, cashGap: cash - x.reserve, monthly: remaining(x.rate), stress1: remaining(x.rate + 1), stress2: remaining(x.rate + 2)};
}
