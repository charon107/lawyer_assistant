/**
 * Typed wrappers over the `/api/litigation/*` Next.js proxy routes.
 *
 * Funnels through the shared `apiClient`; the proxy in
 * `app/api/litigation/[[...path]]/route.ts` forwards to the backend at `/api/v1/litigation/*`.
 */

import { apiClient } from "@/lib/api-client";
import type {
  ColdStartResponse,
  LitigationAnalysis,
  LitigationAnalysisList,
  LitigationDemand,
  LitigationDemandList,
  LitigationMatter,
  LitigationMatterEvent,
  LitigationMatterEventList,
  LitigationMatterList,
  LitigationModuleStatusResponse,
  LitigationNotificationList,
  LitigationProfile,
  PortfolioStatus,
} from "@/types/litigation";

export const litigationApi = {
  // module status
  getStatus: () => apiClient.get<LitigationModuleStatusResponse>("/litigation/status"),

  // cold-start wizard (5 steps)
  submitSetup: (body: Record<string, unknown>) =>
    apiClient.post<ColdStartResponse>("/litigation/setup", body),
  getSetupStatus: () => apiClient.get<ColdStartResponse>("/litigation/setup/status"),

  // profile (customize)
  getProfile: () => apiClient.get<LitigationProfile>("/litigation/profile"),
  updateProfile: (body: Record<string, unknown>) =>
    apiClient.put<LitigationProfile>("/litigation/profile", body),

  // matters
  listMatters: (skip = 0, limit = 50, status?: string) => {
    const qs = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (status) qs.set("status", status);
    return apiClient.get<LitigationMatterList>(`/litigation/matters?${qs.toString()}`);
  },
  createMatter: (body: Record<string, unknown>) =>
    apiClient.post<LitigationMatter>("/litigation/matters", body),
  getMatter: (id: string) => apiClient.get<LitigationMatter>(`/litigation/matters/${id}`),
  updateMatter: (id: string, body: Record<string, unknown>) =>
    apiClient.put<LitigationMatter>(`/litigation/matters/${id}`, body),
  closeMatter: (id: string) =>
    apiClient.post<LitigationMatter>(`/litigation/matters/${id}/close`),
  portfolioStatus: () => apiClient.get<PortfolioStatus>("/litigation/matters/portfolio"),

  // matter events
  listMatterEvents: (matterId: string, skip = 0, limit = 200) => {
    const qs = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    return apiClient.get<LitigationMatterEventList>(
      `/litigation/matters/${matterId}/events?${qs.toString()}`
    );
  },
  createMatterEvent: (matterId: string, body: Record<string, unknown>) =>
    apiClient.post<LitigationMatterEvent>(`/litigation/matters/${matterId}/events`, body),

  // demands
  listDemands: (skip = 0, limit = 50, mode?: string, status?: string) => {
    const qs = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (mode) qs.set("mode", mode);
    if (status) qs.set("status", status);
    return apiClient.get<LitigationDemandList>(`/litigation/demands?${qs.toString()}`);
  },
  createDemand: (body: Record<string, unknown>) =>
    apiClient.post<LitigationDemand>("/litigation/demands", body),
  getDemand: (id: string) => apiClient.get<LitigationDemand>(`/litigation/demands/${id}`),
  updateDemand: (id: string, body: Record<string, unknown>) =>
    apiClient.put<LitigationDemand>(`/litigation/demands/${id}`, body),

  // analyses (history; written by WS agent)
  listAnalyses: (
    skip = 0,
    limit = 50,
    analysisType?: string,
    matterId?: string
  ) => {
    const qs = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (analysisType) qs.set("analysis_type", analysisType);
    if (matterId) qs.set("matter_id", matterId);
    return apiClient.get<LitigationAnalysisList>(`/litigation/analyses?${qs.toString()}`);
  },
  getAnalysis: (id: string) =>
    apiClient.get<LitigationAnalysis>(`/litigation/analyses/${id}`),

  // notifications
  listNotifications: (skip = 0, limit = 50) =>
    apiClient.get<LitigationNotificationList>(
      `/litigation/notifications?skip=${skip}&limit=${limit}`
    ),
  markNotificationRead: (id: string) =>
    apiClient.post<unknown>(`/litigation/notifications/${id}/read`),
};
