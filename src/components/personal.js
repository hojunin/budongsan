import {monthlyPayment} from "./budget.js";

// 모든 금액은 만원, 금리는 연 %다.
export function personalScenario(v) {
  const keys = ["price", "cash", "income", "living", "debt", "housing", "loan", "rate", "years", "cost", "reserve"];
  if (keys.some((k) => v[k] === "" || v[k] == null || !Number.isFinite(Number(v[k])) || Number(v[k]) < 0)) return null;
  const x = Object.fromEntries(keys.map((k) => [k, Number(v[k])]));
  if (!Number.isInteger(x.years) || x.years < 1 || x.years > 50 || x.loan > x.price || x.rate > 100) return null;
  const payment = (rate) => monthlyPayment(x.loan, rate, x.years);
  if (v.depositBefore === true && (v.deposit === "" || v.deposit == null)) return null;
  const deposit = v.deposit === "" || v.deposit == null ? 0 : Number(v.deposit);
  const drop = v.incomeDrop === "" || v.incomeDrop == null ? null : Number(v.incomeDrop);
  const priceDrop = v.priceDrop === "" || v.priceDrop == null ? null : Number(v.priceDrop);
  if (!Number.isFinite(deposit) || deposit < 0 || (drop !== null && (!Number.isFinite(drop) || drop < 0 || drop > 100)) || (priceDrop !== null && (!Number.isFinite(priceDrop) || priceDrop < 0 || priceDrop > 100))) return null;
  const cash = x.cash + (v.depositBefore === true ? deposit : 0) - (x.price - x.loan) - x.cost;
  const remaining = (rate) => x.income - x.living - x.debt - x.housing - payment(rate);
  const result = {cash, cashGap: cash - x.reserve, monthly: remaining(x.rate), stress1: remaining(x.rate + 1), stress2: remaining(x.rate + 2)};
  if (drop !== null) result.incomeStress = result.monthly - x.income * drop / 100;
  if (priceDrop !== null) { result.assessedPrice = x.price * (1 - priceDrop / 100); result.assessedEquity = result.assessedPrice - x.loan; }
  return Object.values(result).every(Number.isFinite) ? result : null;
}
