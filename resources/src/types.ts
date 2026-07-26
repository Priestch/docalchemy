export interface SourceDocumentDTO {
  id: string;
  name: string;
  mime_type: string;
  size_bytes: number;
  storage_key: string;
  checksum: string;
  page_count: number;
  page_dimensions: { page_index: number; width: number; height: number }[];
  uploaded_by: string | null;
  slug: string;
  created_at: string;
  updated_at: string;
}

export interface LatestRunSummary {
  id: string;
  provider_id: string;
  status: 'pending' | 'queued' | 'running' | 'success' | 'failed' | 'cancelled';
  created_at: string;
}

export interface DocumentRunsDTO {
  document_id: string;
  runs: LatestRunSummary[];
}

export interface SourceDocumentListDTO {
  items: SourceDocumentDTO[];
  document_runs: DocumentRunsDTO[];
  total: number;
  offset: number;
  limit: number;
}

export interface AnalysisRunDTO {
  id: string;
  source_document_id: string;
  provider_id: string;
  provider_version: string;
  status: 'pending' | 'queued' | 'running' | 'success' | 'failed' | 'cancelled';
  requested_config: Record<string, any>;
  runtime_metadata: Record<string, any> | null;
  started_at: string | null;
  finished_at: string | null;
  error_code: string | null;
  error_message: string | null;
  artifacts: AnalysisArtifactDTO[];
  created_at: string;
  updated_at: string;
}

export interface CreateAnalysisRunDTO {
  provider_id: string;
  config: Record<string, any>;
}

export interface AnalysisArtifactDTO {
  id: string;
  artifact_type: 'raw_json' | 'raw_markdown' | 'raw_html' | 'render_document';
  format: string;
}

export interface RenderDocument {
  provider_metadata: Record<string, any>;
  pages: { page_index: number; width: number; height: number; children: string[] }[];
  blocks: {
    id: string;
    block_type: 'paragraph' | 'heading' | 'list_item' | 'table' | 'figure' | 'caption' | 'page_header' | 'page_footer' | 'formula' | 'key_value_area' | 'code' | 'footnote' | 'toc';
    text: string;
    heading_level: number | null;
    bbox: { x0: number; y0: number; x1: number; y1: number };
    page_index: number;
    reading_order: number;
    confidence: number | null;
    children: string[];
  }[];
  tables: {
    block_id: string;
    rows: number;
    cols: number;
    cells: {
      row_index: number;
      col_index: number;
      row_span: number;
      col_span: number;
      text: string;
      bbox: { x0: number; y0: number; x1: number; y1: number };
      is_header: boolean;
    }[];
  }[];
  cell_bbox_mode: 'exact' | 'text_extent' | 'none';
  figures: {
    block_id: string;
    image_storage_key: string | null;
    description: string | null;
  }[];
  reading_order: string[];
}

export interface ProviderDefinition {
  provider_id: string;
  display_name: string;
  version: string;
  capabilities: {
    has_ocr: boolean;
    has_table_extraction: boolean;
    has_reading_order: boolean;
    has_formula: boolean;
    has_image_description: boolean;
  };
  supported_mime_types: string[];
  max_pages: number | null;
}
