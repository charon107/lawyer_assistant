/**
 * Types for the litigation-legal (争议解决) module.
 */

export type ModuleStatus = "not_started" | "in_progress" | "completed";
export type SetupDepth = "quick" | "full";

export type UserRole = "lawyer" | "non_lawyer_with_counsel" | "non_lawyer_without";
export type PracticeRole = "企业法务" | "律所律师" | "独立执业" | "其他";
export type PartyRole = "原告方" | "被告方" | "兼顾-默认原告" | "兼顾-默认被告" | "依案件而定";

export type MatterStatus =
  | "active"
  | "settled"
  | "dismissed"
  | "judgment_won"
  | "judgment_lost"
  | "withdrawn"
  | "closed"
  | "archived";
export type MatterStage = "庭前" | "证据交换" | "庭审" | "上诉" | "执行";
export type OurSide = "plaintiff" | "defendant" | "third_party";
export type Risk = "低" | "中" | "高" | "严重";

export type EventType =
  | "procedure"
  | "evidence"
  | "substantive"
  | "strategy"
  | "risk_reassessment"
  | "party"
  | "administrative"
  | "deadline"
  | "closing";
export type DeadlineStatus = "pending" | "approaching" | "overdue" | "met" | "waived";

export type DemandType =
  | "payment"
  | "breach_cure"
  | "stop_infringement"
  | "evidence_preservation"
  | "settlement"
  | "other";
export type DemandMode = "send" | "receive";
export type DemandStatus =
  | "intake"
  | "drafting"
  | "gated"
  | "sent"
  | "received"
  | "responded"
  | "escalated"
  | "closed";
export type SentVia = "邮件" | "快递" | "当面";

export type AnalysisType =
  | "matter_briefing"
  | "chronology"
  | "claim_chart"
  | "subpoena_triage"
  | "legal_hold"
  | "oc_status"
  | "brief_section"
  | "deposition_prep"
  | "privilege_log";
export type Severity = "blocking" | "high" | "medium" | "low";
export type AnalysisStatus = "draft" | "final";

export type NotificationType = "docket_alert" | "deadline_alert" | "manual";
export type Priority = "high" | "medium" | "low" | "normal";

// --- Response types ---

export interface LitigationModuleStatusResponse {
  module_name: string;
  setup_status: ModuleStatus;
  configured: boolean;
}

export interface ColdStartStepData {
  answers?: Record<string, string>;
  seed_files?: string[];
  completed?: boolean;
}

export interface ColdStartPartialConfig {
  steps?: Record<string, ColdStartStepData>;
  quick_mode?: boolean;
  latest_step?: number;
  profile_content?: string;
  [key: string]: unknown;
}

export interface ColdStartResponse {
  step: number;
  progress: number;
  completed: boolean;
  partial_config: ColdStartPartialConfig;
}

export interface LitigationProfile {
  id: string;
  user_id: string;
  company_context?: Record<string, unknown> | null;
  key_contacts?: Record<string, unknown> | null;
  user_role: UserRole;
  lawyer_contact?: string | null;
  practice_role: PracticeRole;
  party_role: PartyRole;
  integrations?: Record<string, unknown> | null;
  risk_calibration?: Record<string, unknown> | null;
  dispute_profile?: Record<string, unknown> | null;
  doc_style?: Record<string, unknown> | null;
  output_config?: Record<string, unknown> | null;
  setup_depth: SetupDepth;
  setup_status: ModuleStatus;
  setup_progress?: Record<string, unknown> | null;
  profile_content?: string | null;
  created_at: string;
}

export interface LitigationMatter {
  id: string;
  user_id: string;
  case_name?: string | null;
  case_number?: string | null;
  court?: string | null;
  cause_of_action?: string | null;
  case_type?: string | null;
  jurisdiction?: string | null;
  our_side?: OurSide | null;
  counterparty?: string | null;
  status: MatterStatus;
  stage?: MatterStage | null;
  risk?: Risk | null;
  materiality?: string | null;
  exposure_range?: string | null;
  filing_date?: string | null;
  next_deadline?: string | null;
  outside_counsel?: Record<string, unknown> | null;
  internal_owners?: Record<string, unknown> | null;
  conflicts?: Record<string, unknown> | null;
  initial_theory?: string | null;
  notes?: string | null;
  source: string;
  closed_date?: string | null;
  outcome?: string | null;
  final_cost?: string | null;
  lessons?: string | null;
  created_at: string;
}

export interface LitigationMatterList {
  items: LitigationMatter[];
  total: number;
}

export interface LitigationMatterEvent {
  id: string;
  matter_id: string;
  user_id: string;
  event_date?: string | null;
  event_type: EventType;
  summary?: string | null;
  field_changes?: Record<string, [unknown, unknown]> | null;
  due_date?: string | null;
  deadline_status?: DeadlineStatus | null;
  associated_files?: string[] | null;
  created_at: string;
}

export interface LitigationMatterEventList {
  items: LitigationMatterEvent[];
  total: number;
}

export interface LitigationDemand {
  id: string;
  user_id: string;
  matter_id?: string | null;
  demand_type: DemandType;
  mode: DemandMode;
  counterparty?: string | null;
  intake_snapshot?: Record<string, unknown> | null;
  right_or_claim?: Record<string, unknown> | null;
  letter_draft?: string | null;
  outbound_letter?: string | null;
  pretransmit_checklist?: Record<string, unknown> | null;
  response_deadline?: string | null;
  triage_result?: Record<string, unknown> | null;
  recommended_action?: string | null;
  status: DemandStatus;
  escalation_flag: boolean;
  escalation_reason?: string | null;
  sent_date?: string | null;
  sent_via?: SentVia | null;
  log?: Record<string, unknown>[] | null;
  created_at: string;
}

export interface LitigationDemandList {
  items: LitigationDemand[];
  total: number;
}

export interface LitigationAnalysis {
  id: string;
  user_id: string;
  matter_id?: string | null;
  analysis_type: AnalysisType;
  subject?: string | null;
  counterparty?: string | null;
  classification?: string | null;
  severity?: Severity | null;
  result_summary?: string | null;
  result_memo?: string | null;
  result_json?: Record<string, unknown> | null;
  status: AnalysisStatus;
  created_at: string;
}

export interface LitigationAnalysisList {
  items: LitigationAnalysis[];
  total: number;
}

export interface LitigationNotification {
  id: string;
  user_id: string;
  notification_type: NotificationType;
  title: string;
  content?: string | null;
  priority: Priority;
  is_read: boolean;
  action_url?: string | null;
  created_at: string;
}

export interface LitigationNotificationList {
  items: LitigationNotification[];
  total: number;
}

export interface PortfolioStatus {
  total: number;
  active: number;
  closed: number;
  by_status: Record<string, number>;
  by_risk: Record<string, number>;
  by_stage: Record<string, number>;
  stale_count: number;
  overdue_deadlines: number;
  anomalies: {
    stale: number;
    overdue: number;
    high_risk: number;
    no_events: number;
    no_deadline: number;
    no_risk: number;
    no_stage: number;
  };
}

// --- WS types ---

export type LitigationWsAction =
  | "matter_briefing"
  | "demand_draft"
  | "demand_received"
  | "subpoena_triage"
  | "legal_hold"
  | "chronology"
  | "claim_chart"
  | "oc_status"
  | "brief_section"
  | "deposition_prep"
  | "privilege_log";

export interface LitigationWsMessage {
  action: LitigationWsAction;
  prompt: string;
  matter_id?: string;
  demand_id?: string;
}

export type LitigationWsEvent =
  | { type: "analysis_started"; data: { analysis_id: string } }
  | { type: "text_delta"; data: { content: string } }
  | {
      type: "tool_call";
      data: { tool_call_id: string; tool_name: string; args: Record<string, unknown> };
    }
  | { type: "tool_result"; data: { tool_call_id: string; content: string } }
  | { type: "final_result"; data: { output: string } }
  | { type: "complete"; data: Record<string, unknown> }
  | { type: "error"; data: { message: string; code?: string } };
