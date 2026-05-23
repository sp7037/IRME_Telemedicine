/** Sticky header height used to position fixed sidebar below header (keep in sync with Header padding). */
export const DASHBOARD_HEADER_OFFSET_PX = 56;

/** Desktop sidebar widths — Sidebar uses box-sizing: border-box so these are full outer width. */
export const SIDEBAR_WIDTH_EXPANDED_PX = 250;
export const SIDEBAR_WIDTH_COLLAPSED_PX = 72;

/** Space between sidebar right edge and main text (avoids shadow / hover clipping content). */
export const SIDEBAR_TO_MAIN_GUTTER_PX = 12;

export function dashboardContentMarginLeft(isNarrow, sidebarCollapsed) {
  if (isNarrow) return 0;
  return (sidebarCollapsed ? SIDEBAR_WIDTH_COLLAPSED_PX : SIDEBAR_WIDTH_EXPANDED_PX) + SIDEBAR_TO_MAIN_GUTTER_PX;
}
