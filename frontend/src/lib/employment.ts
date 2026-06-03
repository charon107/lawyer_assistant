/**
 * Typed wrappers over the `/api/employment/*` Next.js proxy routes.
 *
 * Funnels through the shared `apiClient`; the proxy in
 * `app/api/employment/[[...path]]/route.ts` forwards to the backend at
 * `/api/v1/employment/*`.
 */

import { apiClient } from "@/lib/api-client";
import type {
  ColdStartResponse,
  EmploymentModuleStatusResponse,
  EmploymentNotificationList,
  EmploymentReview,
  EmploymentReviewList,
  Expansion,
  ExpansionList,
  Investigation,
  InvestigationDetail,
  InvestigationList,
  LeaveRegistration,
  LeaveRegistrationList,
} from "@/types/employment";

export const employmentApi = {
  getStatus: () =>
    apiClient.get<EmploymentModuleStatusResponse>("/employment/status"),

  // cold-start wizard
  submitSetup: (body: Record<string, unknown>) =>
    apiClient.post<ColdStartResponse>("/employment/setup", body),
  getSetupStatus: () => apiClient.get<ColdStartResponse>("/employment/setup/status"),

  // profile
  getProfile: () => apiClient.get<Record<string, unknown>>("/employment/profile"),
  updateProfile: (body: Record<string, unknown>) =>
    apiClient.put<Record<string, unknown>>("/employment/profile", body),

  // reviews (history; written by WS agent)
  listReviews: (skip = 0, limit = 50) =>
    apiClient.get<EmploymentReviewList>(`/employment/reviews?skip=${skip}&limit=${limit}`),
  getReview: (id: string) => apiClient.get<EmploymentReview>(`/employment/reviews/${id}`),

  // leaves
  listLeaves: (skip = 0, limit = 50) =>
    apiClient.get<LeaveRegistrationList>(`/employment/leaves?skip=${skip}&limit=${limit}`),
  createLeave: (body: Record<string, unknown>) =>
    apiClient.post<LeaveRegistration>("/employment/leaves", body),
  updateLeave: (id: string, body: Record<string, unknown>) =>
    apiClient.put<LeaveRegistration>(`/employment/leaves/${id}`, body),

  // investigations
  listInvestigations: (skip = 0, limit = 50) =>
    apiClient.get<InvestigationList>(`/employment/investigations?skip=${skip}&limit=${limit}`),
  openInvestigation: (body: Record<string, unknown>) =>
    apiClient.post<Investigation>("/employment/investigations", body),
  getInvestigation: (id: string) =>
    apiClient.get<InvestigationDetail>(`/employment/investigations/${id}`),
  addLogEntry: (id: string, body: Record<string, unknown>) =>
    apiClient.post<unknown>(`/employment/investigations/${id}/entries`, body),

  // expansions
  listExpansions: (skip = 0, limit = 50) =>
    apiClient.get<ExpansionList>(`/employment/expansions?skip=${skip}&limit=${limit}`),
  createExpansion: (body: Record<string, unknown>) =>
    apiClient.post<Expansion>("/employment/expansions", body),
  updateExpansion: (id: string, body: Record<string, unknown>) =>
    apiClient.put<Expansion>(`/employment/expansions/${id}`, body),

  // notifications
  listNotifications: (skip = 0, limit = 50) =>
    apiClient.get<EmploymentNotificationList>(
      `/employment/notifications?skip=${skip}&limit=${limit}`
    ),
  markNotificationRead: (id: string) =>
    apiClient.post<unknown>(`/employment/notifications/${id}/read`),
};
