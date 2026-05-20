/**
 * LPA Case types.
 */

export interface Case {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  status: string;
  document_type: string;
  document_count: number;
  created_at: string;
  updated_at: string | null;
}

export interface CaseDetail extends Case {
  documents: Document[];
}

export interface Document {
  id: string;
  filename: string;
  mime_type: string;
  file_type: string;
  size: number;
  summary: string | null;
  has_parsed_content: boolean;
  created_at: string;
}

export interface CaseListResponse {
  items: Case[];
  total: number;
}

export interface DocumentListResponse {
  items: Document[];
  total: number;
}

// Backward compatibility aliases
export type LPACase = Case;
export type LPACaseDetail = CaseDetail;
export type LPADocument = Document;
export type LPACaseListResponse = CaseListResponse;
export type LPADocumentListResponse = DocumentListResponse;
