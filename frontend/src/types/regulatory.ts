/**
 * Types for the regulatory-legal (监管合规) module.
 */

export type ModuleStatus = "not_started" | "in_progress" | "completed";
export type SetupDepth = "quick" | "full";

export type UserRole = "lawyer" | "non_lawyer_with_counsel" | "non_lawyer_without";
export type PracticeSetting = "独立执业" | "中大型律所" | "法务内部" | "政府法援诊所";

export type ItemType =
  | "regulation"
  | "normative"
  | "nprm"
  | "pre_rule"
  | "enforcement"
  | "guidance"
  | "speech"
  | "settlement"
  | "other";
export type Materiality = "always" | "review" | "fyi";
export type MaterialitySource = "auto_rule" | "llm" | "user";
export type RegItemStatus = "new" | "triaged" | "diffed" | "archived";

export type AnalysisType = "policy_diff" | "policy_redraft";
export type Severity = "blocking" | "high" | "medium" | "low";
export type AnalysisStatus = "draft" | "final";

export type GapType = "none" | "partial" | "full" | "new-policy" | "watch" | "comment-decision";
export type GapStatus = "open" | "in-progress" | "closed" | "risk-accepted";

export type CommentDecision = "undecided" | "filing" | "not-filing" | "filed" | "waived";

export type NotificationType =
  | "reg_digest"
  | "gap_alert"
  | "comment_alert"
  | "gap_assignment"
  | "manual";
export type Priority = "high" | "medium" | "low" | "normal";

// --- Response types ---

export interface RegulatoryModuleStatusResponse {
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

export interface RegulatoryProfile {
  id: string;
  user_id: string;
  company_context?: Record<string, unknown> | null;
  user_role: UserRole;
  lawyer_contact?: string | null;
  practice_setting: PracticeSetting;
  watchlist?: unknown[] | Record<string, unknown> | null;
  policy_library?: unknown[] | Record<string, unknown> | null;
  materiality_threshold?: Record<string, unknown> | null;
  feed_config?: unknown[] | Record<string, unknown> | null;
  gap_response?: Record<string, unknown> | null;
  integrations?: Record<string, unknown> | null;
  output_config?: Record<string, unknown> | null;
  last_feed_check_at?: string | null;
  setup_depth: SetupDepth;
  setup_status: ModuleStatus;
  setup_progress?: Record<string, unknown> | null;
  profile_content?: string | null;
  created_at: string;
}

export interface RegulatoryRegItem {
  id: string;
  user_id: string;
  regulator?: string | null;
  title?: string | null;
  item_type: ItemType;
  materiality: Materiality;
  materiality_source: MaterialitySource;
  summary?: string | null;
  relevance_hook?: string | null;
  link?: string | null;
  published_date?: string | null;
  effective_date?: string | null;
  comment_deadline?: string | null;
  source_tag?: string | null;
  source_name?: string | null;
  status_verified: boolean;
  dedup_key?: string | null;
  status: RegItemStatus;
  created_at: string;
}

export interface RegulatoryRegItemList {
  items: RegulatoryRegItem[];
  total: number;
}

export interface RegulatoryAnalysis {
  id: string;
  user_id: string;
  reg_item_id?: string | null;
  analysis_type: AnalysisType;
  subject?: string | null;
  regulation_name?: string | null;
  policy_affected?: string | null;
  severity?: Severity | null;
  scope_limited: boolean;
  scope_note?: string | null;
  status_verified: boolean;
  result_summary?: string | null;
  result_memo?: string | null;
  result_json?: Record<string, unknown> | unknown[] | null;
  status: AnalysisStatus;
  created_at: string;
}

export interface RegulatoryAnalysisList {
  items: RegulatoryAnalysis[];
  total: number;
}

export interface RegulatoryGap {
  id: string;
  user_id: string;
  reg_item_id?: string | null;
  analysis_id?: string | null;
  requirement?: string | null;
  regulation?: string | null;
  regulation_citation?: string | null;
  policy_affected?: string | null;
  gap_type: GapType;
  severity?: Severity | null;
  owner?: string | null;
  owner_contact?: string | null;
  opened?: string | null;
  due?: string | null;
  status_verified: boolean;
  status: GapStatus;
  notified: boolean;
  resolution?: string | null;
  accepted_by?: string | null;
  accepted_rationale?: string | null;
  created_at: string;
}

export interface RegulatoryGapStatusReport {
  overdue: RegulatoryGap[];
  due_soon: RegulatoryGap[];
  open_gaps: RegulatoryGap[];
  observations: RegulatoryGap[];
  in_progress: RegulatoryGap[];
  recently_closed: RegulatoryGap[];
  by_owner: Record<string, number>;
  earliest_open_due?: string | null;
  suggest_dashboard: boolean;
}

export interface RegulatoryComment {
  id: string;
  user_id: string;
  reg_item_id?: string | null;
  regulation?: string | null;
  regulator?: string | null;
  summary?: string | null;
  link?: string | null;
  comment_deadline?: string | null;
  detected?: string | null;
  decision: CommentDecision;
  owner?: string | null;
  owner_contact?: string | null;
  notified: boolean;
  rationale?: string | null;
  filed_at?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface RegulatoryCommentList {
  items: RegulatoryComment[];
  total: number;
  pending_within_30d: number;
}

export interface RegulatoryNotification {
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

export interface RegulatoryNotificationList {
  items: RegulatoryNotification[];
  total: number;
}

// --- WS types ---

export type RegulatoryWsAction = "reg_feed_watch" | "policy_diff" | "policy_redraft";

export interface RegulatoryWsMessage {
  action: RegulatoryWsAction;
  prompt: string;
  reg_item_id?: string;
}

export type RegulatoryWsEvent =
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
