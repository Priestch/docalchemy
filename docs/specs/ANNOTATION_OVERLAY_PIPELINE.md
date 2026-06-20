# Annotation Overlay Pipeline

## Purpose

This document describes how `RenderDocument` data flows from the backend through the frontend to produce visual annotation overlays on the PDF viewer. It is the authoritative reference for anyone integrating a new provider, modifying the viewer plugin, or customizing overlay styles.

## Architecture

The overlay system has three layers that remain decoupled:

1. **Backend** — Provider-agnostic `RenderDocument` model and per-page annotation API
2. **Plugin** — `@document-kits/viewer` plugin that fetches and transforms annotation data
3. **Viewer** — PDF.js-based viewer that positions and renders custom annotation elements

Each layer owns one coordinate system transformation. Providers only need to produce a valid `RenderDocument` (see `RENDER_DOCUMENT_SCHEMA.md`); the frontend handles the rest automatically.

## Data Flow

```
Provider (Docling, OpenDataLoader, ...)
  ↓ Produces raw output
Normalizer (provider-specific)
  ↓ Converts to RenderDocument (normalized 0-1, top-left origin)
  ↓ Stored as cached JSON in artifact storage
GET /api/analysis-runs/{runId}/render/pages/{pageIndex}/annotations
  ↓ Returns { page: {width, height}, blocks: [...] }
blockAnnotations plugin (createBlockAnnotationPlugin)
  ↓ Fetches per page, converts normalized → PDF annotation rect
  ↓ Attaches resolved style per block_type
  ↓ Returns annotation data objects
@document-kits/viewer PluginManager
  ↓ Routes custom annotation types to registered element classes
  ↓ Instantiates BlockAnnotationElement for each annotation
AnnotationElement._createContainer()
  ↓ Y-flip: PDF coords (bottom-left) → screen coords (top-left)
  ↓ CSS positioning: left%, top%, width%, height%
BlockAnnotationElement.render()
  ↓ Applies background, border, type label badge
  ↓ Returns styled container → appended to annotation layer
```

## Coordinate Transformations

There are exactly three coordinate systems in the pipeline. Each transformation happens at one specific boundary:

### 1. Normalized Coordinates (Backend ↔ API)

- **Origin**: Top-left corner of the page
- **Range**: `[0, 1]` on both axes
- **Owner**: `RenderDocument` (see `RENDER_DOCUMENT_SCHEMA.md`)

The API endpoint returns bounding boxes in this format:

```json
{
  "bbox": { "x0": 0.1, "y0": 0.2, "x1": 0.9, "y1": 0.3 }
}
```

Where `(x0, y0)` is the top-left corner and `(x1, y1)` is the bottom-right corner.

### 2. PDF Annotation Rect (Plugin → Viewer)

- **Origin**: Bottom-left corner of the page (PDF spec)
- **Units**: PDF points (1/72 inch)
- **Format**: `[left, bottom, right, top]`
- **Owner**: The `blockAnnotations` plugin

The plugin converts from normalized to PDF points in `getAnnotations`:

```typescript
rect: [x0 * pageWidth, pageHeight - y1 * pageHeight,
      x1 * pageWidth, pageHeight - y0 * pageHeight]
```

This follows the PDF annotation rect specification where `(left, bottom)` is lower-left and `(right, top)` is upper-right.

### 3. Screen Coordinates (Viewer internal)

- **Origin**: Top-left corner of the page container
- **Units**: CSS percentages
- **Owner**: `@document-kits/viewer` (`AnnotationElement._createContainer`)

The viewer performs the final Y-flip using the page's MediaBox:

```javascript
rect = normalizeRect([
  data.rect[0],                          // left (unchanged)
  page.view[3] - data.rect[1],           // bottom → screen Y
  data.rect[2],                          // right (unchanged)
  page.view[3] - data.rect[3]            // top → screen Y
])
```

Then converts to CSS percentages:

```javascript
style.left   = 100 * rect[0] / pageWidth
style.top    = 100 * rect[1] / pageHeight
style.width  = 100 * (data.rect[2] - data.rect[0]) / pageWidth
style.height = 100 * (data.rect[3] - data.rect[1]) / pageHeight
```

## Required Annotation Data Fields

Each annotation object returned by the plugin's `getAnnotations` must include:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `annotationType` | `string` | Yes | Must match a registered type (`"block-overlay"`) |
| `id` | `string` | Yes | Unique identifier within the page |
| `rect` | `[number, number, number, number]` | Yes | PDF annotation rect `[left, bottom, right, top]` in points |
| `rotation` | `number` | Yes | Must be `0`. If omitted/undefined, the viewer swaps width/height |
| `borderStyle` | `{ width: number }` | Yes | Set `{ width: 0 }` to disable PDF.js border rendering |
| `block_type` | `string` | Yes | Block type from `RenderDocument` (e.g. `"heading"`, `"paragraph"`) |
| `text` | `string` | Yes | Block text content |
| `_resolvedStyle` | `ResolvedBlockStyle` | Yes | Pre-resolved style (bg, label, textColor, borderColor) |

**Why `rotation: 0` is required**: The viewer's `_createContainer` checks `data.rotation === 0` to choose between direct sizing and rotated sizing. When `rotation` is `undefined`, the strict equality `undefined === 0` evaluates to `false`, causing the viewer to enter `setRotation()` which swaps width and height.

## Plugin API

### Factory Function

```typescript
function createBlockAnnotationPlugin(
  runId: string,
  styleConfig?: BlockStyleConfig
): Plugin
```

### Style Configuration

```typescript
interface BlockStyleEntry {
  bg?: string;          // Background color, e.g. "rgba(99, 102, 241, 0.15)"
  label?: string;       // Badge text, e.g. "H", "T", "" for no badge
  textColor?: string;   // Badge text color, e.g. "rgb(79, 70, 229)"
  borderColor?: string; // Border color, e.g. "rgba(99, 102, 241, 0.5)"
}

type BlockStyleConfig = Partial<Record<string, BlockStyleEntry>>
```

Overrides are merged per block type with the defaults. Omitted fields fall back to the default.

### Default Styles

| Block Type | Background | Label | Color |
|------------|-----------|-------|-------|
| `heading` | Indigo 15% | H | Indigo |
| `paragraph` | Gray 8% | | Gray |
| `table` | Green 15% | T | Green |
| `figure` | Blue 15% | F | Blue |
| `caption` | Amber 15% | C | Amber |
| `list_item` | Purple 12% | L | Purple |
| `code` | Gray 12% | </> | Gray |
| `formula` | Pink 12% | = | Pink |
| `page_header` | Sky 10% | | Sky |
| `page_footer` | Sky 10% | | Sky |
| `footnote` | Orange 10% | FN | Orange |
| `toc` | Violet 10% | TOC | Violet |
| `key_value_area` | Teal 10% | KV | Teal |
| *(unknown)* | Gray 8% | | Gray |

### Usage from PdfViewer

```tsx
import { createBlockAnnotationPlugin } from '../plugins/blockAnnotations';
import type { BlockStyleConfig } from '../plugins/blockAnnotations';

// In the viewer component:
const plugins = runId
  ? [createBlockAnnotationPlugin(runId, blockStyleConfig)]
  : [];

createViewerApp({
  parent: container,
  src: pdfUrl,
  resourcePath: '/static/document-viewer',
  plugins,
});
```

## Adding a New Provider

New providers require **no frontend changes** if they produce a valid `RenderDocument`. The pipeline is:

1. Implement `ProviderAdapter.execute()` → produce raw output
2. Implement a normalizer function → convert raw output to `RenderDocument`
3. Ensure all block types use the canonical names from `RENDER_DOCUMENT_SCHEMA.md`
4. Register the provider in `ProviderRegistry`

The existing `blockAnnotations` plugin handles any provider's output because:
- It fetches annotations by `runId` (agnostic to which provider created the run)
- It renders based on `block_type` strings with configurable styles
- Unknown block types fall back to the default gray style

To customize overlay appearance for a specific provider, pass a `BlockStyleConfig` through `PdfViewer`:

```tsx
<PdfViewer
  src={`/api/documents/${id}/download`}
  runId={activeRunId}
  blockStyleConfig={{
    heading: { bg: "rgba(255,0,0,0.2)", borderColor: "red", label: "H1" },
  }}
/>
```
