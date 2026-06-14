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

    this.container.style.pointerEvents = "none";
    this.container.style.overflow = "visible";
    this.container.title = `[${this.data.block_type}] ${this.data.text || ""}`;

    const isTable = this.data.block_type === "table";
    const blockId = this.data.id;
    const overlay = document.createElement("div");
    overlay.style.position = "absolute";
    overlay.style.top = "0";
    overlay.style.left = "0";
    overlay.style.width = "100%";
    overlay.style.height = "100%";
    overlay.style.backgroundColor = "transparent";
    overlay.style.border = isTable
      ? `2px dashed ${style.borderColor}`
      : `2px solid ${style.borderColor}`;
    overlay.style.borderRadius = "4px";
    overlay.style.boxSizing = "border-box";
    overlay.style.pointerEvents = "auto";
    if (!isTable) {
      overlay.style.boxShadow = `0 0 0 2px ${style.bg}`;
    }
    this.container.appendChild(overlay);

    const shortLabel = style.label || this.data.block_type;
    const fullLabel = this.data.block_type;
    const badge = document.createElement("span");
    badge.textContent = shortLabel || "";
    badge.style.position = "absolute";
    badge.style.top = "2px";
    badge.style.right = "2px";
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
      overlay.addEventListener("mouseenter", () => {
        const root = this.container.getRootNode() as ShadowRoot | Document;
        root.querySelectorAll(`[data-table-block="${blockId}"]`).forEach((el) => {
          (el as HTMLElement).style.borderColor = "rgba(59,130,246,0.25)";
        });
      });
      overlay.addEventListener("mouseleave", () => {
        const root = this.container.getRootNode() as ShadowRoot | Document;
        root.querySelectorAll(`[data-table-block="${blockId}"]`).forEach((el) => {
          (el as HTMLElement).style.borderColor = "transparent";
        });
      });
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
    const isHeader: boolean = this.data._isHeader;

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
    cell.style.border = "1px solid transparent";
    cell.style.backgroundColor = "transparent";
    cell.style.transition = "background-color 0.15s ease, border-color 0.15s ease";

    cell.addEventListener("mouseenter", () => {
      cell.style.backgroundColor = isHeader
        ? "rgba(59,130,246,0.18)"
        : "rgba(59,130,246,0.06)";
      cell.style.borderColor = "rgba(59,130,246,0.50)";
    });
    cell.addEventListener("mouseleave", () => {
      cell.style.backgroundColor = "transparent";
      cell.style.borderColor = "transparent";
    });

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
        });
      }

      // Table cell overlays
      for (const table of data.tables) {
        const tableBlock = data.blocks.find(b => b.id === table.block_id);
        const tableBbox = tableBlock?.bbox;

        for (const cell of table.cells) {
          let rect: number[];
          if (cell.bbox) {
            const { x0, y0, x1, y1 } = cell.bbox;
            rect = [x0 * pw, ph - y1 * ph, x1 * pw, ph - y0 * ph];
          } else if (tableBbox && table.cols > 0 && table.rows > 0) {
            const colW = (tableBbox.x1 - tableBbox.x0) / table.cols;
            const rowH = (tableBbox.y1 - tableBbox.y0) / table.rows;
            const cx0 = tableBbox.x0 + cell.col_index * colW;
            const cy0 = tableBbox.y0 + cell.row_index * rowH;
            const cx1 = cx0 + cell.col_span * colW;
            const cy1 = cy0 + cell.row_span * rowH;
            rect = [cx0 * pw, ph - cy1 * ph, cx1 * pw, ph - cy0 * ph];
          } else {
            continue;
          }
          annotations.push({
            annotationType: "table-cell",
            id: `${table.block_id}-cell-${cell.row_index}-${cell.col_index}`,
            rect,
            borderStyle: { width: 0 },
            rotation: 0,
            _isHeader: cell.is_header,
            _tableBlockId: table.block_id,
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
