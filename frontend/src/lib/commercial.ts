/**
 * Typed wrappers over the `/api/commercial/*` Next.js proxy routes.
 *
 * Every method funnels through the shared `apiClient` so error
 * handling + base-URL handling stay consistent with the rest of the
 * app. The proxy in `app/api/commercial/[[...path]]/route.ts`
 * forwards to the backend at `/api/v1/commercial/*`.
 */

import { apiClient } from "@/lib/api-client";
import type {
  ClauseDeviationCountList,
  ColdStartRequest,
  ColdStartResponse,
  CommercialMatter,
  CommercialMatterCreate,
  CommercialMatterList,
  CommercialMatterUpdate,
  CommercialProfile,
  CommercialProfileUpdate,
  ContractReview,
  ContractReviewList,
  ModuleStatusResponse,
  PlaybookProposal,
  PlaybookProposalList,
  PlaybookProposalUpdate,
  RenewalRegistration,
  RenewalRegistrationCreate,
  RenewalRegistrationList,
  RenewalRegistrationUpdate,
} from "@/types/commercial";

export const commercialApi = {
  getStatus: () =>
    apiClient.get<ModuleStatusResponse>("/commercial/status"),

  getSetupStatus: () =>
    apiClient.get<ColdStartResponse>("/commercial/setup/status"),

  submitSetupStep: (req: ColdStartRequest) =>
    apiClient.post<ColdStartResponse>("/commercial/setup", req),

  getProfile: () =>
    apiClient.get<CommercialProfile>("/commercial/profile"),

  updateProfile: (data: CommercialProfileUpdate) =>
    apiClient.put<CommercialProfile>("/commercial/profile", data),

  listReviews: (skip = 0, limit = 50) =>
    apiClient.get<ContractReviewList>(
      `/commercial/reviews?skip=${skip}&limit=${limit}`,
    ),

  getReview: (id: string) =>
    apiClient.get<ContractReview>(`/commercial/reviews/${id}`),

  // ----- Matters -----------------------------------------------------------

  listMatters: (skip = 0, limit = 50) =>
    apiClient.get<CommercialMatterList>(
      `/commercial/matters?skip=${skip}&limit=${limit}`,
    ),

  createMatter: (data: CommercialMatterCreate) =>
    apiClient.post<CommercialMatter>("/commercial/matters", data),

  getMatter: (id: string) =>
    apiClient.get<CommercialMatter>(`/commercial/matters/${id}`),

  updateMatter: (id: string, data: CommercialMatterUpdate) =>
    apiClient.patch<CommercialMatter>(`/commercial/matters/${id}`, data),

  // ----- Renewals ----------------------------------------------------------

  listRenewals: (skip = 0, limit = 50) =>
    apiClient.get<RenewalRegistrationList>(
      `/commercial/renewals?skip=${skip}&limit=${limit}`,
    ),

  registerRenewal: (data: RenewalRegistrationCreate) =>
    apiClient.post<RenewalRegistration>("/commercial/renewals", data),

  updateRenewal: (id: string, data: RenewalRegistrationUpdate) =>
    apiClient.patch<RenewalRegistration>(`/commercial/renewals/${id}`, data),

  // ----- Deviations (aggregated) -------------------------------------------

  listClauseDeviationCounts: () =>
    apiClient.get<ClauseDeviationCountList>("/commercial/deviations"),

  // ----- Playbook proposals ------------------------------------------------

  listProposals: (skip = 0, limit = 50) =>
    apiClient.get<PlaybookProposalList>(
      `/commercial/proposals?skip=${skip}&limit=${limit}`,
    ),

  updateProposal: (id: string, data: PlaybookProposalUpdate) =>
    apiClient.patch<PlaybookProposal>(`/commercial/proposals/${id}`, data),
};
