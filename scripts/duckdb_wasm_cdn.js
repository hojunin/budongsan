// 빌드 후처리: DuckDB wasm(34~39 MiB)은 Cloudflare Pages 파일당 25 MiB 제한을 넘는다.
// dist 에서 wasm 을 지우고, stdlib/duckdb.js 가 jsDelivr 의 같은 버전을 받도록 경로를 바꾼다.
import {readdirSync, readFileSync, rmSync, writeFileSync} from "node:fs";

const dir = "dist/_observablehq/stdlib";
const re = /\.\.\/\.\.\/_npm\/(@duckdb\/duckdb-wasm@[^/]+)\/dist\/(duckdb-(?:eh|mvp)\.wasm)/g;
let count = 0;
for (const name of readdirSync(dir).filter((n) => /^duckdb\..*\.js$/.test(n))) {
  const path = `${dir}/${name}`;
  const src = readFileSync(path, "utf8");
  const out = src.replace(re, (_, pkg, file) => {
    count++;
    rmSync(`dist/_npm/${pkg}/dist/${file}`, {force: true});
    return `https://cdn.jsdelivr.net/npm/${pkg}/dist/${file}`;
  });
  writeFileSync(path, out);
}
// Framework 가 경로 형식을 바꾸면 조용히 25 MiB 초과로 배포가 깨지므로 여기서 멈춘다.
if (count !== 2) throw new Error(`duckdb wasm 경로를 ${count}개 바꿈 (2개 예상)`);
console.log("duckdb wasm → jsDelivr");
