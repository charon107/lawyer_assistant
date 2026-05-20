"use client";

import { useCallback, useState } from "react";

export interface AdminUserDetail {
  id: string;
  email: string;
  full_name: string | null;
  role: "admin" | "user";
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
  avatar_url: string | null;
}

export interface AdminUserListResponse {
  items: AdminUserDetail[];
  total: number;
}

export interface UserUpdatePayload {
  email?: string;
  full_name?: string;
  password?: string;
  role?: "admin" | "user";
  is_active?: boolean;
}

export function useAdminUsers() {
  const [users, setUsers] = useState<AdminUserDetail[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = useCallback(
    async (params?: { skip?: number; limit?: number; search?: string }) => {
      setIsLoading(true);
      setError(null);
      try {
        const query = new URLSearchParams();
        if (params?.skip) query.set("skip", String(params.skip));
        if (params?.limit) query.set("limit", String(params.limit));
        if (params?.search) query.set("search", params.search);

        const res = await fetch(`/api/admin/users?${query.toString()}`, {
          credentials: "include",
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail || `Failed to fetch users: ${res.status}`);
        }
        const data: AdminUserListResponse = await res.json();
        setUsers(data.items);
        setTotal(data.total);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load users");
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const updateUser = useCallback(
    async (userId: string, payload: UserUpdatePayload): Promise<AdminUserDetail> => {
      const res = await fetch(`/api/admin/users/${userId}`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Failed to update user: ${res.status}`);
      }
      return await res.json();
    },
    []
  );

  return {
    users,
    total,
    isLoading,
    error,
    fetchUsers,
    updateUser,
  };
}
