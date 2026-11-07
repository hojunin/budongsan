# Interactive data UI

Approved outcome: replace basic tables and charts with libraries; support compact mobile-friendly filters, table search/sort/filters and multiple chart indicators.

- Tabulator: shared table component, column filters, global search, localized pagination, responsive row details; replace both Inputs.table callers. Preserve safe text formatting and numeric/date sorting.
- ECharts: shared lifecycle/theme/resize component; replace all Plot charts on five pages. Keep statistical ranges, canceled trades, reference lines and budget markers. Add legend selection, zoom, reset and image export. Market overview combines volume/price; regional comparison permits several indicators on separate axes (or normalized indices).
- Compact controls: segmented radios, slim toggle, small chips, compact filter rows. Keep iOS input font size, visible focus and mobile usable targets.
- Verify: production build; all pages 320/390/1440px; table search/sort/collapse/reset; chart legends/zoom/multi-indicator updates; theme/reduced-motion/lifecycle disposal; empty selections.

No backend, financial formulas or data collection changes. Shared libraries must dispose on Observable invalidation.

Implemented: Tabulator 6.7.1, ECharts 6.1.0 and Tom Select 2.6.2. Native selects now support searching and multi-select chips; radios use segmented labels and the toggle is a small switch. All five chart pages migrated, including ranges, reference lines, medians and budget markers. Both interactive tables migrated. Static dictionary tables remain simple HTML.

Verified: production build; 18 page/viewport combinations; global and column table filtering (including mobile input events), numeric sorting, reset, responsive row expansion; chart legend toggling, zoom and normalized multiple indicators; Select keyboard search/add and empty selections. Manually checked chart image export and instance disposal, and dark mobile layout. UI enhancement cleanup is bound to the same Observable cell as initialization so reactive invalidation does not strand plain controls.

Local preview stays on port 3000. No data collection, credential changes or deployment were performed. Physical mobile devices remain untested.
