import { AnnotationElement } from "@document-kits/viewer";

// --- Public Types ---

export interface BlockStyleEntry {
  bg?: string;
  hoverBg?: string;
  label?: string;
  textColor?: string;
  borderColor?: string;
}

export type BlockStyleConfig = Partial<Record<string, BlockStyleEntry>>;

// --- Internal Types ---

interface ResolvedBlockStyle {
  bg: string;
  hoverBg: string;
  label: string;
  textColor: string;
  borderColor: string;
}

interface BlockData {
  id: string;
  block_type: string;
  text: string;
  heading_level: number | null;
  bbox: { x0: number; y0: number; x1: number; y1: number } | null;
  page_index: number;
}

interface TableCellData {
  row_index: number;
  col_index: number;
  row_span: number;
  col_span: number;
  text: string;
  bbox: { x0: number; y0: number; x1: number; y1: number } | null;
  is_header: boolean;
}

interface TableData {
  block_id: string;
  rows: number;
  cols: number;
  cells: TableCellData[];
}

interface PageAnnotationsResponse {
  page: { width: number; height: number } | null;
  blocks: BlockData[];
  tables: TableData[];
  cell_bbox_mode: "exact" | "text_extent" | "none";
}

// --- Semantic color palette ---
// Grouped into families rather than a rainbow per type

const RED = "#ef4444";
const RED_BG = "rgba(239,68,68,0.06)";
const RED_HOVER = "rgba(239,68,68,0.12)";

const C = {
  neutral:    { bg: RED_BG, hoverBg: RED_HOVER, border: RED, text: RED },
  heading:    { bg: RED_BG, hoverBg: RED_HOVER, border: RED, text: RED },
  data:       { bg: RED_BG, hoverBg: RED_HOVER, border: RED, text: RED },
  accent:     { bg: RED_BG, hoverBg: RED_HOVER, border: RED, text: RED },
  code:       { bg: RED_BG, hoverBg: RED_HOVER, border: RED, text: RED },
};

// --- Default Styles ---

const DEFAULT_STYLE: ResolvedBlockStyle = {
  bg: C.neutral.bg,
  hoverBg: C.neutral.hoverBg,
  label: "",
  textColor: C.neutral.text,
  borderColor: C.neutral.border,
};

const DEFAULT_BLOCK_STYLES: Record<string, ResolvedBlockStyle> = {
  heading:       { ...C.heading, label: "H",  textColor: C.heading.text,  borderColor: C.heading.border },
  paragraph:     { ...C.neutral, label: "",   textColor: C.neutral.text,  borderColor: C.neutral.border },
  table:         { ...C.data,    label: "T",  textColor: C.data.text,     borderColor: C.data.border },
  figure:        { ...C.data,    label: "F",  textColor: C.data.text,     borderColor: C.data.border },
  caption:       { ...C.accent,  label: "C",  textColor: C.accent.text,   borderColor: C.accent.border },
  list_item:     { ...C.neutral, label: "L",  textColor: C.neutral.text,  borderColor: C.neutral.border },
  code:          { ...C.code,    label: "</>",textColor: C.code.text,      borderColor: C.code.border },
  formula:       { ...C.accent,  label: "Σ",  textColor: C.accent.text,   borderColor: C.accent.border },
  page_header:   { ...C.neutral, label: "",   textColor: C.neutral.text,  borderColor: C.neutral.border },
  page_footer:   { ...C.neutral, label: "",   textColor: C.neutral.text,  borderColor: C.neutral.border },
  footnote:      { ...C.accent,  label: "FN", textColor: C.accent.text,   borderColor: C.accent.border },
  toc:           { ...C.neutral, label: "TOC",textColor: C.neutral.text,  borderColor: C.neutral.border },
  key_value_area:{ ...C.data,    label: "KV", textColor: C.data.text,     borderColor: C.data.border },
};

// --- Cell grid-line animation (exact-mode / OpenDataLoader cells) ---
// Injected into the viewer's root (handles shadow DOM). "Marching ants" — an
// animated dashed outline that walks around each cell — is the canonical
// selection/highlight animation and reads as far more attention-grabbing than
// a static or breathing border. The per-cell background (which edges to draw)
// is set inline so shared internal edges are drawn by exactly one cell.
const CELL_MARCH_STYLE_ID = 'docalchemy-cell-march-style';
const CELL_MARCH_CLASS = 'docalchemy-cell-march';
const MARCH_ON = 'rgba(239,68,68,0.95)';
const MARCH_OFF = 'rgba(239,68,68,0)';
function ensureCellMarchStyle(root: ShadowRoot | Document) {
  const r = root as ShadowRoot;
  if (r.querySelector?.(`#${CELL_MARCH_STYLE_ID}`)) return;
  const style = document.createElement('style');
  style.id = CELL_MARCH_STYLE_ID;
  style.textContent = `
    .${CELL_MARCH_CLASS} {
      animation: docalchemy-march 0.8s linear infinite;
    }
    @keyframes docalchemy-march {
      /* Animate only the dash offset along each edge; keep the perpendicular
         axis pinned so every edge (incl. bottom/right) stays in place.
         Layer order must match marchCellBackground(): top, bottom, left, right. */
      from { background-position: 0 0, 0 100%, 0 0, 100% 0; }
      to   { background-position: 12px 0, 12px 100%, 0 12px, 100% 12px; }
    }
  `;
  if (root === document) document.head.appendChild(style);
  else r.appendChild(style);
}

// Build the 4-edge marching-ants background for one cell. Top + left are
// always drawn; bottom only when the cell is in the last row, right only when
// in the last column — so shared internal edges are owned by exactly one cell
// and the grid has no doubled lines.
function marchCellBackground(isLastRow: boolean, isLastCol: boolean): string {
  const hDash = (color: string) =>
    `repeating-linear-gradient(90deg, ${color} 0 6px, ${MARCH_OFF} 6px 12px)`;
  const vDash = (color: string) =>
    `repeating-linear-gradient(0deg, ${color} 0 6px, ${MARCH_OFF} 6px 12px)`;
  return [
    `${hDash(MARCH_ON)} 0 0 / 12px 1.5px repeat-x`,
    `${hDash(isLastRow ? MARCH_ON : MARCH_OFF)} 0 100% / 12px 1.5px repeat-x`,
    `${vDash(MARCH_ON)} 0 0 / 1.5px 12px repeat-y`,
    `${vDash(isLastCol ? MARCH_ON : MARCH_OFF)} 100% 0 / 1.5px 12px repeat-y`,
  ].join(', ');
}

// --- Annotation Element ---

class BlockAnnotationElement extends AnnotationElement {
  declare data: any;
  declare container: HTMLElement;

  constructor(parameters: any) {
    super(parameters, { isRenderable: true, ignoreBorder: true });
  }

  render() {
    // Filter: hide if annotation belongs to a different viewer.
    // Deferred — container isn't in the DOM yet during render().
    const runId = this.data._runId;
    setTimeout(() => {
      let el: HTMLElement | null = this.container;
      while (el) {
        const viewerRunId = el.getAttribute('data-docalchemy-run');
        if (viewerRunId) {
          if (viewerRunId !== runId) {
            this.container.style.display = "none";
          }
          break;
        }
        el = el.parentElement;
      }
    }, 0);

    const style: ResolvedBlockStyle = this.data._resolvedStyle;

    // For tables we need the container to receive hover events so we can
    // toggle per-cell highlights without the overlay covering the cells.
    // For non-table blocks keep pointer events disabled on the container
    // and let the overlay capture hover.
    const isTable = this.data.block_type === "table";
    // Clear any container-level border/styles that the viewer may have
    // applied for annotation rendering; we want full control over visuals
    // for table annotations.
    if (isTable) {
      (this.container as HTMLElement).style.border = 'none';
      (this.container as HTMLElement).style.outline = 'none';
      (this.container as HTMLElement).style.boxShadow = 'none';
    }

    // Remove any previously attached overlays or cell elements from
    // earlier renders to avoid duplicate visuals.
    this.container.querySelectorAll('[data-block-overlay]').forEach((n) => n.remove());
    this.container.querySelectorAll('[data-table-cell]').forEach(n => n.remove());
    this.container.style.pointerEvents = isTable ? "auto" : "none";
    this.container.style.overflow = "visible";
    this.container.title = `[${this.data.block_type}] ${this.data.text || ""}`;
    const blockId = this.data.id;
    const overlay = document.createElement("div");
    overlay.setAttribute('data-block-overlay', '');
    overlay.style.position = "absolute";
    overlay.style.top = "0";
    overlay.style.left = "0";
    overlay.style.width = "100%";
    overlay.style.height = "100%";
    overlay.style.backgroundColor = "transparent";
    // Tables show a solid outline by default; on hover the solid border is
    // removed and the marching-ants cell grid takes over (for grid tables).
    // Non-table blocks keep a solid border.
    overlay.style.border = isTable ? `1px solid ${style.borderColor}` : `2px solid ${style.borderColor}`;
    overlay.style.borderRadius = "4px";
    overlay.style.boxSizing = "border-box";
    // The overlay should not cover the table cells visually when
    // highlighting per-cell backgrounds. For tables we set the overlay
    // to pointerEvents: none and listen for hover on the container so
    // cell elements remain visible above it.
    overlay.style.pointerEvents = isTable ? "none" : "auto";
    if (!isTable) {
      overlay.style.boxShadow = `0 0 0 2px ${style.bg}`;
    }
    this.container.appendChild(overlay);

    const shortLabel = style.label || this.data.block_type;
    const fullLabel = this.data.block_type;
    const badge = document.createElement("span");
    badge.textContent = shortLabel || "";
    badge.style.position = "absolute";
    badge.style.top = "-2px";
    badge.style.left = "100%";
    badge.style.marginLeft = "2px";
    badge.style.fontSize = "9px";
    badge.style.fontWeight = "500";
    badge.style.fontFamily = "system-ui, sans-serif";
    badge.style.lineHeight = "1.3";
    badge.style.padding = "1px 5px";
    badge.style.backgroundColor = style.borderColor;
    badge.style.color = "#fff";
    badge.style.borderRadius = "3px";
    badge.style.whiteSpace = "nowrap";
    badge.style.letterSpacing = "0.03em";
    badge.style.pointerEvents = "none";
    badge.style.transition = "opacity 0.12s ease";
    if (!shortLabel) badge.style.display = "none";
    overlay.appendChild(badge);

    if (isTable) {
      overlay.dataset.tableBlockBoundary = blockId;
      // Render per-cell overlays if present on the annotation data. We
      // attach these to the table container so they align with the
      // table overlay rect. Cell rects are given in page pixels and are
      // relative to the container's rect computed by the viewer.
      const root = this.container.getRootNode() as ShadowRoot | Document;
      ensureCellMarchStyle(root);

      const renderCells = () => {
        // Remove any previous cell highlights
        this.container.querySelectorAll('[data-table-cell]').forEach(n => n.remove());

        const tableCells = (this.data._tableCells as any[]) || [];
        for (const c of tableCells) {
          const cellEl = document.createElement('div');
          cellEl.setAttribute('data-table-cell', '');
          cellEl.style.position = 'absolute';

          const tb = c._tableBbox || { x0: 0, x1: 1, y0: 0, y1: 1 };
          const tableWidthNorm = tb.x1 - tb.x0 || 1;
          const tableHeightNorm = tb.y1 - tb.y0 || 1;

          // cell normalized coords relative to page. Render-doc convention
          // is y-DOWN from the page top: y0 = top edge (smaller), y1 = bottom
          // edge (larger). Ensure ordering so widths/heights are positive.
          const cellX0 = Math.min(c.x0, c.x1);
          const cellX1 = Math.max(c.x0, c.x1);
          const cellYTop = Math.min(c.y0, c.y1);
          const cellYBottom = Math.max(c.y0, c.y1);

          // Relative position inside the table as fractions (0..1). Cells are
          // sized in PERCENTAGES of the container, so they reflow on zoom/
          // resize via normal layout — no container measurement and no
          // ResizeObserver needed.
          const relLeft = (cellX0 - tb.x0) / tableWidthNorm;
          const relRight = (cellX1 - tb.x0) / tableWidthNorm;
          const relTop = (cellYTop - tb.y0) / tableHeightNorm;
          const relBottom = (cellYBottom - tb.y0) / tableHeightNorm;

          // exact-mode providers (OpenDataLoader) emit true cell boxes that
          // tile the table, so we draw their edges as a grid: full-size cells
          // with a border, NO fill (text stays visible underneath). Other
          // modes (Docling text extents) use a translucent fill with a small
          // inset gap so adjacent fills don't merge into one block.
          const gridMode = c.mode === 'exact';
          const CELL_GAP_PX = gridMode ? 0 : 2;
          const wPct = (relRight - relLeft) * 100;
          const hPct = (relBottom - relTop) * 100;

          cellEl.style.left = `${relLeft * 100}%`;
          cellEl.style.top = `${relTop * 100}%`;
          cellEl.style.width = CELL_GAP_PX ? `calc(${wPct}% - ${CELL_GAP_PX}px)` : `${wPct}%`;
          cellEl.style.height = CELL_GAP_PX ? `calc(${hPct}% - ${CELL_GAP_PX}px)` : `${hPct}%`;
          cellEl.style.backgroundColor = 'transparent';
          cellEl.style.opacity = '0';
          cellEl.style.pointerEvents = 'none';
          cellEl.style.zIndex = '3';
          cellEl.style.transition = 'background-color 0.12s ease, opacity 0.12s ease, border-color 0.12s ease';
          cellEl.dataset.bboxMode = c.exact ? 'exact' : (c.mode || 'none');
          cellEl.dataset.cellStyle = gridMode ? 'grid' : 'fill';
          // No border: the marching-ants grid is drawn by background
          // gradients. A transparent border would inset the background by
          // 1px (box-sizing: border-box -> padding-box), making shared
          // internal edges render as two parallel lines 2px apart.
          cellEl.style.border = 'none';
          cellEl.style.boxSizing = 'border-box';
          if (gridMode) {
            // Per-cell edge ownership: top + left always; bottom only on the
            // last row, right only on the last column. Shared internal edges
            // are drawn once -> no doubled ant lines.
            cellEl.style.background = marchCellBackground(!!c.isLastRow, !!c.isLastCol);
          }
          // Tooltip for debugging: show row/col and bbox mode
          const titleParts = [];
          if (typeof c.row_index === 'number' && typeof c.col_index === 'number') titleParts.push(`R:${c.row_index} C:${c.col_index}`);
          if (c._isHeader) titleParts.push('header');
          if (c.mode) titleParts.push(c.mode);
          if (titleParts.length) cellEl.title = titleParts.join(' — ');
          cellEl.style.cursor = 'pointer';
          this.container.appendChild(cellEl);
        }
      };

      renderCells();

      // Whether this table has a marching-ants cell grid (exact-mode). On
      // hover we drop the solid outline so the animated grid (which also
      // draws the outer perimeter via edge ownership) replaces it. Fill-only
      // tables (Docling) keep their solid outline while hovered.
      const tableCellsData = (this.data._tableCells as any[]) || [];
      const hasMarchGrid = tableCellsData.some((c: any) => c.mode === 'exact');
      this.container.dataset.tableMarch = hasMarchGrid ? '1' : '0';
      this.container.dataset.tableBorderColor = style.borderColor;

      // Hover handlers: attach at most once per container. The viewer can
      // call render() again on the SAME container (the top-of-render cleanup
      // removes old overlays/cells), so without this guard each render would
      // stack another mouseenter/mouseleave pair — a leak plus duplicate work
      // on every hover.
      if (!(this.container as any)._cellHoverWired) {
        (this.container as any)._cellHoverWired = true;
        const toggleOutline = (solid: boolean) => {
          if (this.container.dataset.tableMarch !== '1') return;
          const ov = this.container.querySelector('[data-block-overlay]') as HTMLElement | null;
          if (!ov) return;
          if (solid) {
            ov.style.border = `1px solid ${this.container.dataset.tableBorderColor || RED}`;
          } else {
            ov.style.border = 'none';
          }
        };
        this.container.addEventListener('mouseenter', () => {
          this.container.querySelectorAll('[data-table-cell]').forEach((el) => {
            const e = el as HTMLElement;
            if (e.dataset.cellStyle === 'grid') {
              // OpenDataLoader: marching-ants grid lines, no covering fill
              // so the underlying PDF text stays fully visible.
              e.classList.add(CELL_MARCH_CLASS);
            } else {
              // Docling (text extents): translucent fill over the text.
              e.style.backgroundColor = 'rgba(59,130,246,0.22)';
            }
            e.style.opacity = '1';
            e.style.pointerEvents = 'auto';
          });
          // Remove the solid outline; the animated grid now draws the border.
          toggleOutline(false);
        });
        this.container.addEventListener('mouseleave', () => {
          this.container.querySelectorAll('[data-table-cell]').forEach((el) => {
            const e = el as HTMLElement;
            if (e.dataset.cellStyle === 'grid') {
              e.classList.remove(CELL_MARCH_CLASS);
            } else {
              e.style.backgroundColor = 'transparent';
            }
            e.style.opacity = '0';
            e.style.pointerEvents = 'none';
          });
          // Restore the solid outline.
          toggleOutline(true);
        });
      }
    } else {
      overlay.addEventListener("mouseenter", () => {
        overlay.style.boxShadow = "none";
        badge.textContent = fullLabel;
      });
      overlay.addEventListener("mouseleave", () => {
        overlay.style.boxShadow = `0 0 0 2px ${style.hoverBg}`;
        badge.textContent = shortLabel || "";
      });
    }

    return this.container;
  }
}

// --- Table Cell Annotation Element ---

class TableCellAnnotationElement extends AnnotationElement {
  declare data: any;
  declare container: HTMLElement;

  constructor(parameters: any) {
    super(parameters, { isRenderable: true, ignoreBorder: true });
  }

  render() {
    this.container.style.pointerEvents = "none";
    this.container.style.overflow = "visible";

    const cell = document.createElement("div");
    cell.dataset.tableBlock = this.data._tableBlockId;
    cell.style.position = "absolute";
    cell.style.top = "0";
    cell.style.left = "0";
    cell.style.width = "100%";
    cell.style.height = "100%";
    cell.style.boxSizing = "border-box";
    // Don't draw borders by default (they produce L-shapes when only
    // top/left are present). Use a transparent background which will
    // be toggled on table hover for a consistent highlight.
    cell.style.border = "none";
    cell.style.backgroundColor = "transparent";
    cell.style.transition = "background-color 0.12s ease, opacity 0.12s ease";
    // Ensure cell annotation sits above the overlay and can be inspected
    // visually; allow pointer events so QA can hover and inspect individual
    // cells if needed.
    cell.style.zIndex = "2";
    cell.style.pointerEvents = "auto";

    this.container.appendChild(cell);
    return this.container;
  }
}

// --- Plugin Factory ---

export function createBlockAnnotationPlugin(runId: string, styleConfig?: BlockStyleConfig) {
  const pageCache = new Map<string, PageAnnotationsResponse>();

  function resolveStyle(blockType: string): ResolvedBlockStyle {
    const base = DEFAULT_BLOCK_STYLES[blockType] ?? DEFAULT_STYLE;
    const override = styleConfig?.[blockType];
    if (!override) return base;
    return {
      bg: override.bg ?? base.bg,
      hoverBg: override.hoverBg ?? base.hoverBg ?? base.bg,
      label: override.label ?? base.label,
      textColor: override.textColor ?? base.textColor,
      borderColor: override.borderColor ?? base.borderColor,
    };
  }

  return {
    name: `block-annotations-${runId}`,

    annotationTypes: {
      "block-overlay": BlockAnnotationElement,
      "table-cell": TableCellAnnotationElement,
    },

    async getAnnotations(pageIndex: number, pdfPage?: any) {
      const cacheKey = `${runId}-${pageIndex}`;
      let data = pageCache.get(cacheKey);

      if (!data) {
        try {
          const resp = await fetch(`/api/analysis-runs/${runId}/render/pages/${pageIndex}/annotations`);
          data = await resp.json();
          pageCache.set(cacheKey, data);
        } catch (e) {
          console.error("[block-annotations] fetch error:", e);
          return [];
        }
      }

      if (!data.page) return [];

      const { width: pw, height: ph } = data.page;
      const annotations: any[] = [];

      // Block overlays
      for (const block of data.blocks) {
        if (!block.bbox) continue;
        const { x0, y0, x1, y1 } = block.bbox;
        annotations.push({
          annotationType: "block-overlay",
          id: block.id,
          rect: [x0 * pw, ph - y1 * ph, x1 * pw, ph - y0 * ph],
          block_type: block.block_type,
          text: block.text,
          heading_level: block.heading_level,
          borderStyle: { width: 0 },
          rotation: 0,
          _runId: runId,
          _resolvedStyle: resolveStyle(block.block_type),
          // Attach table metadata; table cell rects (in page pixels)
          // will be filled below when processing data.tables.
          _tableCells: [],
        });
      }

      // Table cell overlays
      const cellBboxMode = data.cell_bbox_mode ?? "none";

      for (const table of data.tables) {
        const tableBlock = data.blocks.find(b => b.id === table.block_id);
        const tableBbox = tableBlock?.bbox;
        if (!tableBbox || table.rows === 0 || table.cols === 0) continue;

        // --- Build cell rects and attach them to the corresponding
        // block-overlay annotation so the table overlay can render cell
        // highlights itself. We avoid emitting separate "table-cell"
        // annotations so the table annotation fully controls cell visuals.

        // Find the block-overlay annotation we created earlier and
        // populate its _tableCells array with pixel rects for each cell.
        const tableOverlay = annotations.find(a => a.annotationType === 'block-overlay' && a.id === table.block_id);
        if (!tableOverlay) continue;

        // Table bbox in normalized coords
        const tb = tableBbox; // { x0,y0,x1,y1 }
        // Table pixel rect
        const tpx0 = tb.x0 * pw;
        const tpy0 = ph - tb.y1 * ph;
        const tpx1 = tb.x1 * pw;
        const tpy1 = ph - tb.y0 * ph;

        // --- Mode: "text_extent" ---
        // Cell bboxes are text-glyph extents (e.g. Docling). Infer grid
        // edges by placing separators at midpoints between adjacent
        // column/row text extents. The table bbox provides outer edges.
        //
        // --- Mode: "none" ---
        // No cell bboxes at all. Fall back to uniform grid division
        // using the table bbox.

        // Collect text extents per column and row (using normalized coords).
        const colExtents: { min: number; max: number }[] = Array.from(
          { length: table.cols }, () => ({ min: Infinity, max: -Infinity })
        );
        const rowExtents: { min: number; max: number }[] = Array.from(
          { length: table.rows }, () => ({ min: Infinity, max: -Infinity })
        );

        if (cellBboxMode === "text_extent") {
          for (const c of table.cells) {
            if (!c.bbox) continue;
            if (c.col_span === 1) {
              colExtents[c.col_index].min = Math.min(colExtents[c.col_index].min, c.bbox.x0);
              colExtents[c.col_index].max = Math.max(colExtents[c.col_index].max, c.bbox.x1);
            }
            if (c.row_span === 1) {
              rowExtents[c.row_index].min = Math.min(rowExtents[c.row_index].min, c.bbox.y0);
              rowExtents[c.row_index].max = Math.max(rowExtents[c.row_index].max, c.bbox.y1);
            }
          }
        }

        // Build column edges: [edge0, edge1, ..., edgeCols]
        const colEdges: number[] = new Array(table.cols + 1);
        colEdges[0] = tableBbox.x0;
        colEdges[table.cols] = tableBbox.x1;
        for (let i = 0; i < table.cols - 1; i++) {
          const leftMax = colExtents[i].max !== -Infinity ? colExtents[i].max : null;
          const rightMin = colExtents[i + 1].min !== Infinity ? colExtents[i + 1].min : null;
          if (leftMax !== null && rightMin !== null) {
            colEdges[i + 1] = (leftMax + rightMin) / 2;
          } else {
            colEdges[i + 1] = tableBbox.x0 + (tableBbox.x1 - tableBbox.x0) * (i + 1) / table.cols;
          }
        }

        // Build row edges: [edge0, edge1, ..., edgeRows]
        const rowEdges: number[] = new Array(table.rows + 1);
        rowEdges[0] = tableBbox.y0;
        rowEdges[table.rows] = tableBbox.y1;
        for (let i = 0; i < table.rows - 1; i++) {
          const topMax = rowExtents[i].max !== -Infinity ? rowExtents[i].max : null;
          const bottomMin = rowExtents[i + 1].min !== Infinity ? rowExtents[i + 1].min : null;
          if (topMax !== null && bottomMin !== null) {
            rowEdges[i + 1] = (topMax + bottomMin) / 2;
          } else {
            rowEdges[i + 1] = tableBbox.y0 + (tableBbox.y1 - tableBbox.y0) * (i + 1) / table.rows;
          }
        }

        // Create cell pixel rects for each cell and attach to overlay.
        // Each cell rect should hug the provider-reported text extent so
        // you can judge extraction precision: when the cell carries its
        // own bbox (Docling text-extent glyphs, OpenDataLoader exact
        // boxes), use it directly — even in text_extent mode. Only fall
        // back to the inferred/uniform grid for cells that have no bbox
        // (e.g. spanning/empty cells, or whole providers like MinerU).
        for (const cell of table.cells) {
          const hasRealBbox = !!cell.bbox;
          let nx0: number, nx1: number, ny0: number, ny1: number;
          if (hasRealBbox) {
            nx0 = cell.bbox!.x0;
            nx1 = cell.bbox!.x1;
            ny0 = cell.bbox!.y0;
            ny1 = cell.bbox!.y1;
          } else {
            // Use normalized col/row edges computed earlier
            nx0 = colEdges[cell.col_index];
            nx1 = colEdges[Math.min(cell.col_index + cell.col_span, table.cols)];
            ny0 = rowEdges[cell.row_index];
            ny1 = rowEdges[Math.min(cell.row_index + cell.row_span, table.rows)];
          }

          (tableOverlay._tableCells as any).push({
            x0: nx0,
            x1: nx1,
            y0: ny0,
            y1: ny1,
            _isHeader: cell.is_header,
            row_index: cell.row_index,
            col_index: cell.col_index,
            // include table bbox so renderer can compute relative offsets
            _tableBbox: { x0: tb.x0, x1: tb.x1, y0: tb.y0, y1: tb.y1 },
            // Remember how the cell bbox was derived so the UI can show
            // it in a tooltip for debugging.
            mode: cellBboxMode,
            // Whether this cell was positioned from a real provider bbox
            // (vs. an inferred/uniform grid). Drives whether the renderer
            // draws a precise dashed border on hover.
            exact: hasRealBbox,
            // Edge ownership for marching-ants dedup: each internal grid
            // line is shared by two cells, so only one should draw it. A
            // cell always owns its top + left edges; it also owns bottom if
            // it's in the last row and right if in the last column. This
            // makes every grid line (inner + outer) draw exactly once.
            isLastRow: (cell.row_index + (cell.row_span || 1)) >= table.rows,
            isLastCol: (cell.col_index + (cell.col_span || 1)) >= table.cols,
          });
        }
      }

      return annotations;
    },

    onInit() {},

    onDocumentLoad() {},

    onDestroy(app: any) {
      pageCache.clear();
    },
  };
}
