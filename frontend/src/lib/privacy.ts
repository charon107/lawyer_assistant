/**
 * Typed wrappers over the `/api/privacy/*` Next.js proxy routes.
 *
 * Funnels through the shared `apiClient`; the proxy in
 * `app/api/privacy/[[...path]]/route.ts` forwards to the backend at
 * `/api/v1/privacy/*`.
 */

import { apiClient } from "@/lib/api-client";
import type {
  ColdStartResponse,
  PrivacyDsar,
  PrivacyDsarList,
  PrivacyModuleStatusResponse,
  PrivacyNotificationList,
  PrivacyReview,
  PrivacyReviewList,
} from "@/types/privacy";

export const privacyApi = {
  getStatus: () => apiClient.get<PrivacyModuleStatusResponse>("/privacy/status"),

  // cold-start wizard
  submitSetup: (body: Record<string, unknown>) =>
    apiClient.post<ColdStartResponse>("/privacy/setup", body),
  getSetupStatus: () => apiClient.get<ColdStartResponse>("/privacy/setup/status"),

  // profile (customize)
  getProfile: () => apiClient.get<Record<string, unknown>>("/privacy/profile"),
  updateProfile: (body: Record<string, unknown>) =>
    apiClient.put<Record<string, unknown>>("/privacy/profile", body),

  // reviews (history; written by WS agent)
  listReviews: (skip = 0, limit = 50, reviewType?: string) => {
    const qs = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (reviewType) qs.set("review_type", reviewType);
    return apiClient.get<PrivacyReviewList>(`/privacy/reviews?${qs.toString()}`);
  },
  getReview: (id: string) => apiClient.get<PrivacyReview>(`/privacy/reviews/${id}`),

  // DSAR
  listDsar: (skip = 0, limit = 50) =>
    apiClient.get<PrivacyDsarList>(`/privacy/dsar?skip=${skip}&limit=${limit}`),
  createDsar: (body: Record<string, unknown>) =>
    apiClient.post<PrivacyDsar>("/privacy/dsar", body),
  getDsar: (id: string) => apiClient.get<PrivacyDsar>(`/privacy/dsar/${id}`),
  updateDsar: (id: string, body: Record<string, unknown>) =>
    apiClient.put<PrivacyDsar>(`/privacy/dsar/${id}`, body),

  // notifications
  listNotifications: (skip = 0, limit = 50) =>
    apiClient.get<PrivacyNotificationList>(
      `/privacy/notifications?skip=${skip}&limit=${limit}`
    ),
  markNotificationRead: (id: string) =>
    apiClient.post<unknown>(`/privacy/notifications/${id}/read`),
};
