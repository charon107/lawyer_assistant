/**
 * Typed wrappers over the `/api/corporate/*` Next.js proxy routes.
 *
 * Funnels through the shared `apiClient`; the proxy in
 * `app/api/corporate/[[...path]]/route.ts` forwards to the backend at
 * `/api/v1/corporate/*`.
 */

import { apiClient } from "@/lib/api-client";
import type {
  ClosingChecklistItem,
  ClosingChecklistItemList,
  CorporateDeal,
  CorporateDealCreate,
  CorporateDealList,
  CorporateModuleStatusResponse,
  DiligenceIssue,
  DiligenceIssueList,
  MaterialContractItem,
  MaterialContractItemList,
  TabularReviewList,
  VdrDocument,
  VdrDocumentList,
} from "@/types/corporate";

export const corporateApi = {
  getStatus: () =>
    apiClient.get<CorporateModuleStatusResponse>("/corporate/status"),

  listDeals: (skip = 0, limit = 50) =>
    apiClient.get<CorporateDealList>(`/corporate/deals?skip=${skip}&limit=${limit}`),

  createDeal: (data: CorporateDealCreate) =>
    apiClient.post<CorporateDeal>("/corporate/deals", data),

  getDeal: (id: string) => apiClient.get<CorporateDeal>(`/corporate/deals/${id}`),

  closeDeal: (id: string) =>
    apiClient.post<CorporateDeal>(`/corporate/deals/${id}/close`),

  listDiligence: (dealId: string, skip = 0, limit = 100) =>
    apiClient.get<DiligenceIssueList>(
      `/corporate/deals/${dealId}/diligence?skip=${skip}&limit=${limit}`
    ),

  listChecklist: (dealId: string, skip = 0, limit = 100) =>
    apiClient.get<ClosingChecklistItemList>(
      `/corporate/deals/${dealId}/checklist?skip=${skip}&limit=${limit}`
    ),

  listMaterialContracts: (dealId: string, skip = 0, limit = 100) =>
    apiClient.get<MaterialContractItemList>(
      `/corporate/deals/${dealId}/material-contracts?skip=${skip}&limit=${limit}`
    ),

  listTabular: (dealId: string, skip = 0, limit = 50) =>
    apiClient.get<TabularReviewList>(
      `/corporate/deals/${dealId}/tabular?skip=${skip}&limit=${limit}`
    ),

  listVdr: (dealId: string, skip = 0, limit = 100) =>
    apiClient.get<VdrDocumentList>(
      `/corporate/deals/${dealId}/vdr?skip=${skip}&limit=${limit}`
    ),

  // ----- manual create (agent runs also populate these via /ws/corporate) ---

  createVdr: (dealId: string, body: Record<string, unknown>) =>
    apiClient.post<VdrDocument>(`/corporate/deals/${dealId}/vdr`, body),

  createDiligence: (dealId: string, body: Record<string, unknown>) =>
    apiClient.post<DiligenceIssue>(`/corporate/deals/${dealId}/diligence`, body),

  createChecklistItem: (dealId: string, body: Record<string, unknown>) =>
    apiClient.post<ClosingChecklistItem>(`/corporate/deals/${dealId}/checklist`, body),

  createMaterialContract: (dealId: string, body: Record<string, unknown>) =>
    apiClient.post<MaterialContractItem>(
      `/corporate/deals/${dealId}/material-contracts`,
      body
    ),
};
