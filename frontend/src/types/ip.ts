/**
 * Types for the ip-legal (知识产权) module.
 */

export type ModuleStatus = "not_started" | "in_progress" | "completed";
export type ReviewType =
  | "clearance"
  | "fto"
  | "invention"
  | "infringement"
  | "ip_clause"
  | "oss";
export type IpCategory = "trademark" | "copyright" | "patent" | "trade_secret" | "design";
export type Classification =
  | "GREEN"
  | "YELLOW"
  | "RED"
  | "PURSUE"
  | "INVESTIGATE"
  | "REJECT"
  | "IGNORE"
  | "COMMUNICATE"
  | "CEASE_DESIST"
  | "LITIGATE";
export type Severity = "blocking" | "high" | "medium" | "low";
export type UserRole =
  | "attorney"
  | "patent_agent"
  | "non_attorney_with_lawyer"
  | "non_attorney_without";

export type MatterType = "cease_desist" | "takedown";
export type EnforcementMode = "send" | "receive" | "respond" | "counter";
export type EnforcementStatus =
  | "intake"
  | "drafting"
  | "gated"
  | "sent"
  | "responded"
  | "escalated"
  | "closed";

export type AssetType =
  | "trademark"
  | "patent_invention"
  | "patent_utility"
  | "patent_design"
  | "copyright"
  | "domain"
  | "other";
export type AssetStatus = "pending" | "registered" | "granted" | "lapsed" | "abandoned";

export interface IpModuleStatusResponse {
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

export interface IpReview {
  id: string;
  user_id: string;
  review_type: ReviewType;
  subject?: string | null;
  counterparty?: string | null;
  ip_category?: IpCategory | null;
  classification?: Classification | null;
  severity?: Severity | null;
  result_summary?: string | null;
  result_memo?: string | null;
  result_json?: Record<string, unknown> | null;
  status: string;
  created_at: string;
}

export interface IpReviewList {
  items: IpReview[];
  total: number;
}

export interface IpEnforcement {
  id: string;
  user_id: string;
  matter_type: MatterType;
  mode: EnforcementMode;
  counterparty?: string | null;
  right_at_issue?: Record<string, unknown> | null;
  infringement_facts?: string | null;
  due_diligence?: Record<string, unknown> | null;
  response_deadline?: string | null;
  letter_draft?: string | null;
  outbound_letter?: string | null;
  send_gate?: Record<string, unknown> | null;
  recommended_action?: string | null;
  status: EnforcementStatus;
  escalation_flag: boolean;
  escalation_reason?: string | null;
  log?: Record<string, unknown>[] | null;
  created_at: string;
}

export interface IpEnforcementList {
  items: IpEnforcement[];
  total: number;
}

export interface IpPortfolioAsset {
  id: string;
  user_id: string;
  asset_type: AssetType;
  jurisdiction?: string | null;
  title?: string | null;
  owner_entity?: string | null;
  status: AssetStatus;
  application_number?: string | null;
  registration_number?: string | null;
  filing_date?: string | null;
  registration_date?: string | null;
  grant_date?: string | null;
  priority_date?: string | null;
  next_deadlines?: Record<string, unknown>[] | null;
  business_owner?: string | null;
  agent_managed: boolean;
  notes?: string | null;
  source: string;
  created_at: string;
}

export interface IpPortfolioList {
  items: IpPortfolioAsset[];
  total: number;
}

export interface DeadlineEntry {
  id: string;
  asset_type: string;
  jurisdiction?: string | null;
  title?: string | null;
  business_owner?: string | null;
  deadline_type: string;
  due_date?: string | null;
  grace_end?: string | null;
  basis_rule: string;
  status: string;
}

export interface PortfolioReport {
  buckets: Record<string, DeadlineEntry[]>;
  summary: string;
}

export interface PortfolioAudit extends PortfolioReport {
  flags: { asset_id: string; title?: string | null; flag: string }[];
}

export interface IpNotification {
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

export interface IpNotificationList {
  items: IpNotification[];
  total: number;
}

export type IpWsAction =
  | "clearance"
  | "fto"
  | "invention"
  | "infringement"
  | "ip_clause"
  | "oss"
  | "cease_desist"
  | "takedown";

export interface IpWsMessage {
  action: IpWsAction;
  prompt: string;
  subject?: string;
  enforcement_id?: string;
}

export type IpWsEvent =
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
