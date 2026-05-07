"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { apiClient } from "@/lib/api-client";
import type {
  LPACase,
  LPACaseDetail,
  LPADocument,
  LPACaseListResponse,
  LPADocumentListResponse,
} from "@/types";

export function useCases() {
  const [cases, setCases] = useState<LPACase[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCases = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<LPACaseListResponse>("/lpa-cases");
      setCases(response.items);
      setTotal(response.total);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch cases";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createCase = useCallback(
    async (name: string, description?: string): Promise<LPACase | null> => {
      try {
        const response = await apiClient.post<LPACase>("/lpa-cases", {
          name,
          description: description || null,
        });
        setCases((prev) => [response, ...prev]);
        setTotal((prev) => prev + 1);
        toast.success("Case created");
        return response;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to create case";
        toast.error(message);
        return null;
      }
    },
    []
  );

  const deleteCase = useCallback(async (id: string): Promise<boolean> => {
    try {
      await apiClient.delete(`/lpa-cases/${id}`);
      setCases((prev) => prev.filter((c) => c.id !== id));
      setTotal((prev) => prev - 1);
      toast.success("Case deleted");
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to delete case";
      toast.error(message);
      return false;
    }
  }, []);

  return {
    cases,
    total,
    isLoading,
    error,
    fetchCases,
    createCase,
    deleteCase,
  };
}

export function useCaseDetail(caseId: string | null) {
  const [caseDetail, setCaseDetail] = useState<LPACaseDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCase = useCallback(async () => {
    if (!caseId) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<LPACaseDetail>(`/lpa-cases/${caseId}`);
      setCaseDetail(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch case";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    fetchCase();
  }, [fetchCase]);

  const uploadDocument = useCallback(
    async (file: File): Promise<LPADocument | null> => {
      if (!caseId) return null;
      try {
        const formData = new FormData();
        formData.append("file", file);
        const response = await fetch(`/api/lpa-cases/${caseId}/documents`, {
          method: "POST",
          body: formData,
        });
        if (!response.ok) {
          const errorData = await response.json().catch(() => null);
          throw new Error(errorData?.detail || "Upload failed");
        }
        const doc = await response.json();
        setCaseDetail((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            documents: [doc, ...prev.documents],
            document_count: prev.document_count + 1,
          };
        });
        toast.success("Document uploaded");
        return doc;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Upload failed";
        toast.error(message);
        return null;
      }
    },
    [caseId]
  );

  const deleteDocument = useCallback(
    async (docId: string): Promise<boolean> => {
      if (!caseId) return false;
      try {
        await apiClient.delete(`/lpa-cases/${caseId}/documents/${docId}`);
        setCaseDetail((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            documents: prev.documents.filter((d) => d.id !== docId),
            document_count: prev.document_count - 1,
          };
        });
        toast.success("Document deleted");
        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to delete document";
        toast.error(message);
        return false;
      }
    },
    [caseId]
  );

  const refreshDocuments = useCallback(async () => {
    if (!caseId) return;
    try {
      const response = await apiClient.get<LPADocumentListResponse>(
        `/lpa-cases/${caseId}/documents`
      );
      setCaseDetail((prev) => {
        if (!prev) return prev;
        return { ...prev, documents: response.items };
      });
    } catch {
      // ignore refresh errors
    }
  }, [caseId]);

  return {
    caseDetail,
    isLoading,
    error,
    fetchCase,
    uploadDocument,
    deleteDocument,
    refreshDocuments,
  };
}
