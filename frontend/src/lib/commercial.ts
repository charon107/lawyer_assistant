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
  ColdStartRequest,
  ColdStartResponse,
  CommercialProfile,
  CommercialProfileUpdate,
  ContractReview,
  ContractReviewList,
  ModuleStatusResponse,
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
};
