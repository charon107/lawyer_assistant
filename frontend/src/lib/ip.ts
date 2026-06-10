/**
 * Typed wrappers over the `/api/ip/*` Next.js proxy routes.
 *
 * Funnels through the shared `apiClient`; the proxy in
 * `app/api/ip/[[...path]]/route.ts` forwards to the backend at `/api/v1/ip/*`.
 */

import { apiClient } from "@/lib/api-client";
import type {
  ColdStartResponse,
  IpEnforcement,
  IpEnforcementList,
  IpModuleStatusResponse,
  IpNotificationList,
  IpPortfolioAsset,
  IpPortfolioList,
  IpReview,
  IpReviewList,
  PortfolioAudit,
  PortfolioReport,
} from "@/types/ip";

export const ipApi = {
  getStatus: () => apiClient.get<IpModuleStatusResponse>("/ip/status"),

  // cold-start wizard
  submitSetup: (body: Record<string, unknown>) =>
    apiClient.post<ColdStartResponse>("/ip/setup", body),
  getSetupStatus: () => apiClient.get<ColdStartResponse>("/ip/setup/status"),

  // profile (customize)
  getProfile: () => apiClient.get<Record<string, unknown>>("/ip/profile"),
  updateProfile: (body: Record<string, unknown>) =>
    apiClient.put<Record<string, unknown>>("/ip/profile", body),

  // reviews (history; written by WS agent)
  listReviews: (skip = 0, limit = 50, reviewType?: string) => {
    const qs = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (reviewType) qs.set("review_type", reviewType);
    return apiClient.get<IpReviewList>(`/ip/reviews?${qs.toString()}`);
  },
  getReview: (id: string) => apiClient.get<IpReview>(`/ip/reviews/${id}`),

  // enforcement (intake + management; letters drafted via WS)
  listEnforcement: (skip = 0, limit = 50, matterType?: string) => {
    const qs = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (matterType) qs.set("matter_type", matterType);
    return apiClient.get<IpEnforcementList>(`/ip/enforcement?${qs.toString()}`);
  },
  createEnforcement: (body: Record<string, unknown>) =>
    apiClient.post<IpEnforcement>("/ip/enforcement", body),
  getEnforcement: (id: string) => apiClient.get<IpEnforcement>(`/ip/enforcement/${id}`),
  updateEnforcement: (id: string, body: Record<string, unknown>) =>
    apiClient.put<IpEnforcement>(`/ip/enforcement/${id}`, body),

  // portfolio (CRUD + arithmetic report/audit)
  listPortfolio: (skip = 0, limit = 100, assetType?: string) => {
    const qs = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (assetType) qs.set("asset_type", assetType);
    return apiClient.get<IpPortfolioList>(`/ip/portfolio?${qs.toString()}`);
  },
  createPortfolioAsset: (body: Record<string, unknown>) =>
    apiClient.post<IpPortfolioAsset>("/ip/portfolio", body),
  updatePortfolioAsset: (id: string, body: Record<string, unknown>) =>
    apiClient.put<IpPortfolioAsset>(`/ip/portfolio/${id}`, body),
  portfolioReport: () => apiClient.get<PortfolioReport>("/ip/portfolio/report"),
  portfolioAudit: () => apiClient.get<PortfolioAudit>("/ip/portfolio/audit"),

  // notifications
  listNotifications: (skip = 0, limit = 50) =>
    apiClient.get<IpNotificationList>(`/ip/notifications?skip=${skip}&limit=${limit}`),
  markNotificationRead: (id: string) =>
    apiClient.post<unknown>(`/ip/notifications/${id}/read`),
};
