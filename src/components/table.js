import {TabulatorFull as Tabulator} from "npm:tabulator-tables@6.7.1";
import {html} from "npm:htl";

export function dataTable(rows, columns, invalidation) {
  const search = html`<input type="search" placeholder="표에서 검색…" aria-label="표 전체 검색">`;
  const clear = html`<button type="button">초기화</button>`;
  const count = html`<span class="table-count" role="status"></span>`;
  const grid = html`<div class="data-grid" aria-label="검색·정렬 가능한 데이터 표"></div>`;
  const node = html`<section class="data-table"><div class="table-toolbar">${search}${count}${clear}</div>${grid}<p class="table-help">열 제목으로 정렬 · + 버튼으로 숨겨진 항목 보기</p></section>`;
  let table;
  let ready = false;
  const text = (value, column) => column.format ? column.format(value) : value ?? "–";
  const observer = new ResizeObserver(([entry]) => {
    if (!entry.contentRect.width || table) return;
    table = new Tabulator(grid, {
      // Keep filtering and row expansion inside a stable viewport.
      height: 440, data: rows.map((row) => ({...row})), layout: "fitColumns", responsiveLayout: "collapse",
      responsiveLayoutCollapseStartOpen: false, responsiveLayoutCollapseUseFormatters: true,
      responsiveLayoutCollapseFormatter(data) {
        const list = document.createElement("dl");
        for (const item of data) {
          const term = document.createElement("dt"); term.textContent = item.title;
          const detail = document.createElement("dd");
          if (item.value instanceof Node) detail.append(item.value); else detail.textContent = item.value ?? "–";
          list.append(term, detail);
        }
        return list;
      },
      placeholder: "표시할 데이터가 없습니다", pagination: true, paginationSize: 8,
      locale: "ko", langs: {ko: {pagination: {first: "처음", first_title: "첫 페이지", last: "끝", last_title: "마지막 페이지", prev: "이전", prev_title: "이전 페이지", next: "다음", next_title: "다음 페이지", page_title: "페이지"}}},
      columnDefaults: {
        headerFilter(cell, onRendered, success) {
          const input = html`<input type="search" placeholder="필터…" aria-label=${`${cell.getColumn().getDefinition().title} 필터`}>`;
          // Mobile keyboards and paste emit input without a keyup event.
          input.addEventListener("input", () => success(input.value));
          return input;
        },
        minWidth: 110, vertAlign: "middle", resizable: false
      },
      columns: [
        {formatter: "responsiveCollapse", width: 38, minWidth: 38, hozAlign: "center", headerSort: false, headerFilter: false, responsive: 0},
        ...columns.map((column, i) => ({
          title: column.title, field: column.field, sorter: column.sorter ?? "string",
          responsive: column.responsive ?? (i === 0 ? 0 : i + 1), widthGrow: i === 0 ? 1.5 : 1,
          hozAlign: column.sorter === "number" ? "right" : "left",
          formatter: (cell) => html`<span class=${column.signed ? (cell.getValue() > 0 ? "value-up" : cell.getValue() < 0 ? "value-down" : "") : ""}>${text(cell.getValue(), column)}</span>`,
          headerFilterFunc: (query, value) => String(text(value, column)).toLocaleLowerCase().includes(query.toLocaleLowerCase())
        }))
      ]
    });
    table.on("tableBuilt", () => { ready = true; count.textContent = `${rows.length}건`; });
    table.on("dataFiltered", (_, active) => { count.textContent = `${active.length} / ${rows.length}건`; });
  });
  search.addEventListener("input", () => {
    if (!ready) return;
    const query = search.value.trim().toLocaleLowerCase();
    table.setFilter((row) => columns.some((column) => String(text(row[column.field], column)).toLocaleLowerCase().includes(query)));
  });
  clear.addEventListener("click", () => {
    if (!ready) return;
    search.value = ""; table.clearFilter(true); table.clearSort(); table.setPage(1);
  });
  observer.observe(node);
  invalidation.then(() => { observer.disconnect(); table?.destroy(); ready = false; });
  return node;
}
