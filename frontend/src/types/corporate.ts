/**
 * Types for the corporate-legal (公司并购) module. Mirror the backend
 * schemas in `app/schemas/corporate/`.
 */

export type CorporateModule = "mna" | "board" | "public" | "entities";
export type ModuleStatus = "not_started" | "in_progress" | "completed";

export interface CorporateModuleStatusResponse {
  configured: boolean;
  setup_status: ModuleStatus;
  active_modules: CorporateModule[] | null;
}

export type DealStatus = "active" | "closed" | "archived";
export type DealSide = "buyer" | "seller" | "na";
export type Confidentiality = "standard" | "elevated" | "clean_team";

export interface CorporateDeal {
  id: string;
  user_id: string;
  code: string;
  client: string | null;
  counterparty: string | null;
  deal_type: string | null;
  side: DealSide | null;
  confidentiality_level: Confidentiality;
  status: DealStatus;
  key_facts: string | null;
  dataroom_location: string | null;
  materiality_contract: string | null;
  materiality_litigation: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface CorporateDealCreate {
  code: string;
  client?: string | null;
  counterparty?: string | null;
  deal_type?: string | null;
  side?: DealSide | null;
  confidentiality_level?: Confidentiality;
  key_facts?: string | null;
  dataroom_location?: string | null;
  materiality_contract?: string | null;
  materiality_litigation?: string | null;
}

export interface CorporateDealList {
  items: CorporateDeal[];
  total: number;
}

export type Severity = "blocking" | "high" | "medium" | "low";

export interface DiligenceIssue {
  id: string;
  deal_id: string;
  title: string;
  category: string | null;
  severity: Severity;
  source_doc: string | null;
  finding: string | null;
  recommendation: string | null;
  cite: string | null;
  status: "open" | "resolved" | "waived";
  created_at: string;
  updated_at: string | null;
}

export interface DiligenceIssueList {
  items: DiligenceIssue[];
  total: number;
}

export interface ClosingChecklistItem {
  id: string;
  deal_id: string;
  source_issue_id: string | null;
  item_type:
    | "condition"
    | "consent"
    | "document"
    | "filing"
    | "shareholder_vote"
    | "regulatory"
    | "release";
  item: string;
  basis: string | null;
  approval_threshold: string | null;
  responsible: string | null;
  blocking: boolean;
  status: "open" | "in_progress" | "done" | "waived";
  due: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface ClosingChecklistItemList {
  items: ClosingChecklistItem[];
  total: number;
}

export interface TabularReview {
  id: string;
  deal_id: string;
  title: string;
  columns: { key: string; label: string; prompt?: string | null }[] | null;
  rows: Record<string, unknown>[] | null;
  source_docs: string[] | null;
  status: "in_progress" | "completed";
  export_path: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface TabularReviewList {
  items: TabularReview[];
  total: number;
}

export interface MaterialContractItem {
  id: string;
  deal_id: string;
  source_issue_id: string | null;
  contract: string;
  counterparty: string | null;
  threshold_basis: string | null;
  disclosed: boolean;
  cite: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface MaterialContractItemList {
  items: MaterialContractItem[];
  total: number;
}
