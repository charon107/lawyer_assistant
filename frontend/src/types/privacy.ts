/**
 * Types for the privacy-legal (个人信息保护) module.
 */

export type ModuleStatus = "not_started" | "in_progress" | "completed";
export type ReviewType = "triage" | "pia" | "dpa" | "gap" | "policy_sweep";
export type Direction = "entrusted" | "handler";
export type Classification = "PROCEED" | "PIA_REQUIRED" | "DPIA_MANDATORY" | "STOP";
export type Severity = "blocking" | "high" | "medium" | "low";
export type Recommendation =
  | "APPROVED"
  | "WITH_CONDITIONS"
  | "CHANGES_REQUIRED"
  | "NOT_APPROVED";
export type DsarRequestType =
  | "access"
  | "copy"
  | "delete"
  | "correct"
  | "explain"
  | "restrict";
export type DsarStatus =
  | "received"
  | "verifying"
  | "locating"
  | "exemption_analysis"
  | "drafted"
  | "responded"
  | "escalated";
export type UserRole = "attorney" | "non_attorney_with_lawyer" | "non_attorney_without";

export interface PrivacyModuleStatusResponse {
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

export interface PrivacyReview {
  id: string;
  user_id: string;
  review_type: ReviewType;
  subject?: string | null;
  counterparty?: string | null;
  direction?: Direction | null;
  classification?: Classification | null;
  severity?: Severity | null;
  recommendation?: Recommendation | null;
  result_summary?: string | null;
  result_memo?: string | null;
  result_json?: Record<string, unknown> | null;
  status: string;
  created_at: string;
}

export interface PrivacyReviewList {
  items: PrivacyReview[];
  total: number;
}

export interface PrivacyDsar {
  id: string;
  user_id: string;
  request_types?: string[] | null;
  data_subject_ref?: string | null;
  date_received?: string | null;
  date_verified?: string | null;
  date_responded?: string | null;
  response_deadline?: string | null;
  identity_verified: boolean;
  verification_method?: string | null;
  systems_checked?: Record<string, unknown>[] | null;
  exemptions?: Record<string, unknown>[] | null;
  ack_letter?: string | null;
  response_letter?: string | null;
  status: DsarStatus;
  escalation_flag: boolean;
  escalation_reason?: string | null;
  log?: Record<string, unknown>[] | null;
  created_at: string;
}

export interface PrivacyDsarList {
  items: PrivacyDsar[];
  total: number;
}

export interface PrivacyNotification {
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

export interface PrivacyNotificationList {
  items: PrivacyNotification[];
  total: number;
}

export type PrivacyWsAction =
  | "triage"
  | "dpa"
  | "pia"
  | "gap"
  | "dsar"
  | "policy_sweep"
  | "policy_query";

export interface PrivacyWsMessage {
  action: PrivacyWsAction;
  prompt: string;
  subject?: string;
  dsar_id?: string;
}

export type PrivacyWsEvent =
  | { type: "review_started"; data: { review_id: string } }
  | { type: "text_delta"; data: { content: string } }
  | {
      type: "tool_call";
      data: { tool_call_id: string; tool_name: string; args: Record<string, unknown> };
    }
  | { type: "tool_result"; data: { tool_call_id: string; content: string } }
  | { type: "final_result"; data: { output: string } }
  | { type: "complete"; data: Record<string, unknown> }
  | { type: "error"; data: { message: string; code?: string } };
