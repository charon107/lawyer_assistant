/**
 * Types for the employment-legal (劳动用工) module.
 */

export type ModuleStatus = "not_started" | "in_progress" | "completed";
export type ReviewType =
  | "hiring"
  | "termination"
  | "worker_classification"
  | "policy"
  | "wage_hour"
  | "handbook";
export type LeaveType =
  | "annual"
  | "maternity"
  | "sick"
  | "work_injury"
  | "marriage"
  | "parental"
  | "paternity";
export type InvestigationType = "HR" | "financial" | "executive" | "whistleblower" | "other";
export type InvestigationStatus = "open" | "investigating" | "memo_draft" | "closed";
export type EmploymentStructure = "direct" | "labor_dispatch" | "outsourcing";

export interface EmploymentModuleStatusResponse {
  module_name: string;
  setup_status: ModuleStatus;
  configured: boolean;
}

export interface ColdStartResponse {
  step: number;
  progress: number;
  completed: boolean;
  partial_config: Record<string, unknown>;
  next_questions?: string[] | null;
}

export interface EmploymentReview {
  id: string;
  user_id: string;
  review_type: ReviewType;
  employee_name?: string | null;
  position?: string | null;
  jurisdiction?: string | null;
  result_status?: string | null;
  result_summary?: string | null;
  result_memo?: string | null;
  high_risk_flags?: string[] | null;
  required_approver?: string | null;
  created_at: string;
}

export interface EmploymentReviewList {
  items: EmploymentReview[];
  total: number;
}

export interface LeaveRegistration {
  id: string;
  user_id: string;
  employee_name?: string | null;
  position?: string | null;
  jurisdiction: string;
  leave_type: LeaveType;
  leave_start: string;
  expected_return?: string | null;
  medical_period_end?: string | null;
  maternity_return_date?: string | null;
  work_injury_period_end?: string | null;
  annual_carryover_deadline?: string | null;
  entitlement?: string | null;
  status: "active" | "completed" | "cancelled";
  created_at: string;
}

export interface LeaveRegistrationList {
  items: LeaveRegistration[];
  total: number;
}

export interface LogEntry {
  id: string;
  investigation_id: string;
  entry_seq: number;
  entry_type?: string | null;
  date_of_event?: string | null;
  source?: string | null;
  significance?: string | null;
  summary?: string | null;
  quote?: string | null;
  created_at: string;
}

export interface InvestigationSource {
  id: string;
  source_seq: number;
  source: string;
  status: string;
  notes?: string | null;
}

export interface InvestigationGap {
  id: string;
  gap_seq: number;
  description: string;
  priority: string;
  status: string;
}

export interface Investigation {
  id: string;
  user_id: string;
  investigation_name: string;
  allegation?: string | null;
  investigation_type?: InvestigationType | null;
  status: InvestigationStatus;
  attorney_directed: boolean;
  memo?: string | null;
  created_at: string;
}

export interface InvestigationDetail extends Investigation {
  log_entries: LogEntry[];
  sources: InvestigationSource[];
  gaps: InvestigationGap[];
}

export interface InvestigationList {
  items: Investigation[];
  total: number;
}

export interface Expansion {
  id: string;
  user_id: string;
  slug: string;
  province: string;
  headcount?: string | null;
  position_types?: string[] | null;
  employment_structure?: EmploymentStructure | null;
  analysis_result?: Record<string, unknown> | null;
  tracking_items?: Record<string, unknown>[] | null;
  status: "active" | "completed" | "cancelled";
  created_at: string;
}

export interface ExpansionList {
  items: Expansion[];
  total: number;
}

export interface EmploymentNotification {
  id: string;
  user_id: string;
  kind: string;
  title: string;
  body?: string | null;
  priority: string;
  action_url?: string | null;
  read: boolean;
  created_at: string;
}

export interface EmploymentNotificationList {
  items: EmploymentNotification[];
  total: number;
}

export type EmploymentWsAction =
  | "hiring"
  | "termination"
  | "classification"
  | "policy"
  | "wage_hour"
  | "handbook"
  | "expansion_analyze"
  | "inv_add"
  | "inv_query"
  | "inv_memo"
  | "inv_summary";

export interface EmploymentWsMessage {
  action: EmploymentWsAction;
  prompt: string;
  investigation_id?: string;
  expansion_id?: string;
}

export type EmploymentWsEvent =
  | { type: "text_delta"; data: { content: string } }
  | { type: "tool_call"; data: { tool_call_id: string; tool_name: string; args: Record<string, unknown> } }
  | { type: "tool_result"; data: { tool_call_id: string; content: string } }
  | { type: "final_result"; data: { output: string } }
  | { type: "complete"; data: Record<string, unknown> }
  | { type: "error"; data: { message: string; code?: string } };
