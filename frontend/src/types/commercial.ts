/**
 * TypeScript mirrors of backend `app/schemas/commercial/*`.
 *
 * Keep field names in lockstep with the Pydantic models — the API
 * proxies pass JSON through unchanged.
 */

export type Side = "sales" | "purchasing" | "both";

export type ModuleStatus = "not_started" | "in_progress" | "completed";

export type ResultStatus = "in_progress" | "green" | "yellow" | "red";

export type ReviewType = "vendor" | "nda" | "saas";

export interface PlaybookEntry {
  clause_key: string;
  label: string;
  standard: string;
  floor?: string | null;
  never_accept?: string | null;
  notes?: string | null;
}

export interface Playbook {
  side: Side;
  entries: PlaybookEntry[];
}

export interface EscalationRule {
  clause_key?: string | null;
  min_severity: "low" | "medium" | "high" | "critical";
  approver_role: string;
  channel: "email" | "slack" | "feishu" | "meeting" | "other";
  notes?: string | null;
}

export interface CommercialProfile {
  id: string;
  user_id: string;
  company_name?: string | null;
  entity_type?: string | null;
  team_size?: string | null;
  gc_name?: string | null;
  monthly_volume?: string | null;
  side: Side;
  setup_status: ModuleStatus;
  profile_content?: string | null;
  playbook_sales?: Playbook | null;
  playbook_purchasing?: Playbook | null;
  escalation_matrix?: EscalationRule[] | null;
  renewal_alert_channel?: string | null;
  output_destination?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface CommercialProfileUpdate {
  company_name?: string | null;
  entity_type?: string | null;
  team_size?: string | null;
  gc_name?: string | null;
  monthly_volume?: string | null;
  side?: Side | null;
  setup_status?: ModuleStatus | null;
  profile_content?: string | null;
  playbook_sales?: Playbook | null;
  playbook_purchasing?: Playbook | null;
  escalation_matrix?: EscalationRule[] | null;
  renewal_alert_channel?: string | null;
  output_destination?: string | null;
}

export interface ModuleStatusResponse {
  configured: boolean;
  setup_status: ModuleStatus;
  side: Side | null;
}

// ----- Cold start ----------------------------------------------------------

export type ColdStartStep = 0 | 1 | 2 | 3 | 4;

export interface ColdStartRequest {
  step: ColdStartStep;
  answers: Record<string, unknown>;
  seed_files?: string[];
  quick_mode?: boolean;
}

export interface ColdStartResponse {
  step: ColdStartStep;
  progress: number;
  completed: boolean;
  partial_config: Record<string, unknown>;
  next_questions?: string[] | null;
}

// ----- Contract reviews ----------------------------------------------------

export type DeviationCategory =
  | "missing"
  | "weaker_than_standard"
  | "weaker_than_floor"
  | "non_standard"
  | "unacceptable";

export type SeverityLevel = "green" | "yellow" | "orange" | "red";

export interface SeverityAxis {
  legal_risk: SeverityLevel;
  commercial: SeverityLevel;
}

export interface DeviationItem {
  clause_key: string;
  clause_label: string;
  playbook_position: string;
  contract_quote: string;
  category: DeviationCategory;
  severity: SeverityAxis;
  why_it_matters: string;
  suggested_rewrite?: string | null;
  fallback?: string | null;
}

export interface ContractReviewResult {
  summary: string;
  deviations: DeviationItem[];
  favorable_terms: string[];
  missing_terms: string[];
  required_approver?: string | null;
}

export interface ContractReview {
  id: string;
  user_id: string;
  matter_id?: string | null;
  review_type: ReviewType;
  counterparty?: string | null;
  agreement_name?: string | null;
  agreement_type?: string | null;
  side: Side;
  annual_value?: number | null;
  file_path?: string | null;
  file_name?: string | null;
  result_status?: ResultStatus | null;
  result_summary?: string | null;
  result_memo?: string | null;
  result_json?: ContractReviewResult | null;
  stakeholder_summary?: string | null;
  required_approver?: string | null;
  escalation_sent: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface ContractReviewList {
  items: ContractReview[];
  total: number;
}

// ----- WebSocket protocol --------------------------------------------------

export interface CommercialWsStartMessage {
  action: "start";
  review_type?: ReviewType;
  side?: Side;
  counterparty?: string;
  agreement_name?: string;
  agreement_type?: string;
  annual_value?: number;
  contract_text: string;
}

export type CommercialWsEvent =
  | { type: "review_started"; data: { review_id: string } }
  | { type: "text_delta"; data: { content: string } }
  | {
      type: "tool_call";
      data: { tool_call_id: string; tool_name: string; args: Record<string, unknown> };
    }
  | { type: "tool_result"; data: { tool_call_id: string; content: string } }
  | { type: "final_result"; data: { output: string; review_id: string } }
  | { type: "model_request_end"; data: Record<string, never> }
  | { type: "complete"; data: Record<string, never> }
  | { type: "error"; data: { message: string } };
