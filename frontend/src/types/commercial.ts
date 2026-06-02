/**
 * TypeScript mirrors of backend `app/schemas/commercial/*`.
 *
 * Keep field names in lockstep with the Pydantic models — the API
 * proxies pass JSON through unchanged.
 */

export type Side = "sales" | "purchasing" | "both";

export type SetupDepth = "quick" | "full";

export type UsedBy = "lawyer" | "non_lawyer";

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
  setup_depth?: SetupDepth;
  used_by?: UsedBy;
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

// ----- Matters -------------------------------------------------------------

export type MatterStatus = "active" | "closed" | "archived";

export interface CommercialMatter {
  id: string;
  user_id: string;
  counterparty?: string | null;
  matter_name?: string | null;
  agreement_type?: string | null;
  status: MatterStatus;
  owner?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface CommercialMatterCreate {
  counterparty?: string | null;
  matter_name?: string | null;
  agreement_type?: string | null;
  status?: MatterStatus;
  owner?: string | null;
  notes?: string | null;
}

export interface CommercialMatterUpdate {
  counterparty?: string | null;
  matter_name?: string | null;
  agreement_type?: string | null;
  status?: MatterStatus | null;
  owner?: string | null;
  notes?: string | null;
}

export interface CommercialMatterList {
  items: CommercialMatter[];
  total: number;
}

// ----- Renewals ------------------------------------------------------------

export type RenewalDecision = "pending" | "renew" | "terminate" | "renegotiate";

/** Client-side urgency bucket derived from days-left until the cancel deadline. */
export type UrgencyBucket = "red" | "orange" | "yellow" | "green";

export interface RenewalRegistration {
  id: string;
  user_id: string;
  matter_id?: string | null;
  counterparty?: string | null;
  agreement_name?: string | null;
  effective_date: string;
  term_months: number;
  auto_renew: boolean;
  notice_days: number;
  cancel_by_calendar?: string | null;
  cancel_by_effective?: string | null;
  send_by_effective?: string | null;
  decision: RenewalDecision;
  notes?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface RenewalRegistrationCreate {
  matter_id?: string | null;
  counterparty?: string | null;
  agreement_name?: string | null;
  effective_date: string;
  term_months?: number;
  auto_renew?: boolean;
  notice_days?: number;
  decision?: RenewalDecision;
  notes?: string | null;
}

export interface RenewalRegistrationUpdate {
  counterparty?: string | null;
  agreement_name?: string | null;
  effective_date?: string | null;
  term_months?: number | null;
  auto_renew?: boolean | null;
  notice_days?: number | null;
  decision?: RenewalDecision | null;
  notes?: string | null;
}

export interface RenewalRegistrationList {
  items: RenewalRegistration[];
  total: number;
}

// ----- Deviations (aggregated) ---------------------------------------------

export interface ClauseDeviationCount {
  clause_key: string;
  clause_label?: string | null;
  count: number;
}

export interface ClauseDeviationCountList {
  items: ClauseDeviationCount[];
  total: number;
}

// ----- Playbook proposals --------------------------------------------------

export type ProposalStatus = "pending" | "accepted" | "dismissed";

export interface PlaybookProposal {
  id: string;
  user_id: string;
  clause_key: string;
  clause_label?: string | null;
  current_position?: string | null;
  proposed_position?: string | null;
  deviation_count: number;
  status: ProposalStatus;
  rationale?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface PlaybookProposalUpdate {
  status?: ProposalStatus | null;
  proposed_position?: string | null;
  rationale?: string | null;
}

export interface PlaybookProposalList {
  items: PlaybookProposal[];
  total: number;
}

// ----- Notifications (Phase C) ---------------------------------------------

/** Produced by the three scheduled tasks; drives icon + accent rendering. */
export type NotificationType =
  | "renewal_due"
  | "deal_debrief"
  | "playbook_proposal";

export interface CommercialNotification {
  id: string;
  user_id: string;
  type: NotificationType | string;
  title?: string | null;
  payload?: Record<string, unknown> | null;
  read: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface CommercialNotificationList {
  items: CommercialNotification[];
  total: number;
  unread: number;
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

/** summarize / escalate operate on an EXISTING finished review. */
export interface CommercialWsDownstreamMessage {
  action: "summarize" | "escalate";
  review_id: string;
}

export type CommercialWsMessage =
  | CommercialWsStartMessage
  | CommercialWsDownstreamMessage;

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
  | { type: "error"; data: { message: string; code?: string } };
