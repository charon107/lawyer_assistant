/**
 * LPA Case types.
 */

export interface LPACase {
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

export interface LPACaseDetail extends LPACase {
  documents: LPADocument[];
}

export interface LPADocument {
  id: string;
  filename: string;
  mime_type: string;
  file_type: string;
  size: number;
  summary: string | null;
  has_parsed_content: boolean;
  created_at: string;
}

export interface LPACaseListResponse {
  items: LPACase[];
  total: number;
}

export interface LPADocumentListResponse {
  items: LPADocument[];
  total: number;
}
