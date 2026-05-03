/**
 * Application constants.
 */

export const APP_NAME = "LPA 合同审查";
export const APP_DESCRIPTION = "AI 驱动的 LPA 合同审查平台";

// API Routes (Next.js internal routes)
export const API_ROUTES = {
  // Auth
  LOGIN: "/auth/login",
  REGISTER: "/auth/register",
  LOGOUT: "/auth/logout",
  REFRESH: "/auth/refresh",
  ME: "/auth/me",

  // Health
  HEALTH: "/health",

  // Users
  USERS: "/users",

  // Chat (AI Agent)
  CHAT: "/chat",
} as const;

// Navigation routes
export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  REGISTER: "/register",
  DASHBOARD: "/dashboard",
  CHAT: "/chat",
  PROFILE: "/profile",
  REVIEW: "/review",
  SETTINGS: "/settings",
  ADMIN_RATINGS: "/admin/ratings",
  ADMIN_CONVERSATIONS: "/admin/conversations",
} as const;

// WebSocket URL — auto-detect from browser location in production
export function getWsUrl(): string {
  if (typeof window !== "undefined") {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}`;
  }
  return process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
}

// Backend API URL (public, for direct links like API docs)
export const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
