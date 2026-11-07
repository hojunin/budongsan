// 지역·범주 팔레트는 상승·하락 의미색과 별개다.
export const PALETTE = ['#07857d', '#8b5ba7', '#a46b1c', '#687185', '#748d36', '#a05a85'];
const major = {'서울': PALETTE[0], '경기': PALETTE[1], '전국': PALETTE[2], '수도권': PALETTE[3]};
export function regionColor(region) {
  const name = String(region).split('>').at(-1).split(' · ').at(-1).replace(/ 전체$/, '');
  if (major[name]) return major[name];
  let hash = 0;
  for (const c of name) hash = (Math.imul(hash, 31) + c.codePointAt(0)) >>> 0;
  return PALETTE[hash % PALETTE.length];
}
