/**
 * Typed wrappers over the `/api/regulatory/*` Next.js proxy routes.
 *
 * Funnels through the shared `apiClient`; the proxy in
 * `app/api/regulatory/[[...path]]/route.ts` forwards to the backend at
 * `/api/v1/regulatory/*`.
 */

import { apiClient } from "@/lib/api-client";
import type {
  ColdStartResponse,
  RegulatoryAnalysis,
  RegulatoryAnalysisList,
  RegulatoryComment,
  RegulatoryCommentList,
  RegulatoryGap,
  RegulatoryGapStatusReport,
  RegulatoryModuleStatusResponse,
  RegulatoryNotificationList,
  RegulatoryProfile,
  RegulatoryRegItem,
  RegulatoryRegItemList,
} from "@/types/regulatory";

export const regulatoryApi = {
  // module status
  getStatus: () => apiClient.get<RegulatoryModuleStatusResponse>("/regulatory/status"),

  // cold-start wizard (6 steps)
  submitSetup: (body: Record<string, unknown>) =>
    apiClient.post<ColdStartResponse>("/regulatory/setup", body),
  getSetupStatus: () => apiClient.get<ColdStartResponse>("/regulatory/setup/status"),

  // profile (customize)
  getProfile: () => apiClient.get<RegulatoryProfile>("/regulatory/profile"),
  updateProfile: (body: Record<string, unknown>) =>
    apiClient.put<RegulatoryProfile>("/regulatory/profile", body),

  // reg items
  listItems: (skip = 0, limit = 50, materiality?: string, itemType?: string, status?: string) => {
    const qs = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (materiality) qs.set("materiality", materiality);
    if (itemType) qs.set("item_type", itemType);
    if (status) qs.set("status", status);
    return apiClient.get<RegulatoryRegItemList>(`/regulatory/items?${qs.toString()}`);
  },
  createItem: (body: Record<string, unknown>) =>
    apiClient.post<RegulatoryRegItem>("/regulatory/items", body),
  getItem: (id: string) => apiClient.get<RegulatoryRegItem>(`/regulatory/items/${id}`),
  updateItem: (id: string, body: Record<string, unknown>) =>
    apiClient.put<RegulatoryRegItem>(`/regulatory/items/${id}`, body),

  // analyses (history; written by WS agent)
  listAnalyses: (skip = 0, limit = 50, analysisType?: string, regItemId?: string) => {
    const qs = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (analysisType) qs.set("analysis_type", analysisType);
    if (regItemId) qs.set("reg_item_id", regItemId);
    return apiClient.get<RegulatoryAnalysisList>(`/regulatory/analyses?${qs.toString()}`);
  },
  getAnalysis: (id: string) => apiClient.get<RegulatoryAnalysis>(`/regulatory/analyses/${id}`),

  // gap tracker
  gapStatusReport: () => apiClient.get<RegulatoryGapStatusReport>("/regulatory/gaps"),
  createGap: (body: Record<string, unknown>) =>
    apiClient.post<RegulatoryGap>("/regulatory/gaps", body),
  getGap: (id: string) => apiClient.get<RegulatoryGap>(`/regulatory/gaps/${id}`),
  updateGap: (id: string, body: Record<string, unknown>) =>
    apiClient.put<RegulatoryGap>(`/regulatory/gaps/${id}`, body),
  closeGap: (id: string, body: Record<string, unknown>) =>
    apiClient.post<RegulatoryGap>(`/regulatory/gaps/${id}/close`, body),
  acceptGapRisk: (id: string, body: Record<string, unknown>) =>
    apiClient.post<RegulatoryGap>(`/regulatory/gaps/${id}/accept`, body),

  // comment-period tracker
  listComments: (skip = 0, limit = 50, decision?: string) => {
    const qs = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (decision) qs.set("decision", decision);
    return apiClient.get<RegulatoryCommentList>(`/regulatory/comments?${qs.toString()}`);
  },
  decideComment: (id: string, body: Record<string, unknown>) =>
    apiClient.post<RegulatoryComment>(`/regulatory/comments/${id}/decide`, body),

  // notifications
  listNotifications: (skip = 0, limit = 50) =>
    apiClient.get<RegulatoryNotificationList>(
      `/regulatory/notifications?skip=${skip}&limit=${limit}`
    ),
  markNotificationRead: (id: string) =>
    apiClient.post<unknown>(`/regulatory/notifications/${id}/read`),
};
