/**
 * Application constants.
 */

export const APP_NAME = "LexMind";
export const APP_DESCRIPTION = "法律 AI 智能助手";

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
  COMMERCIAL: "/commercial",
  COMMERCIAL_SETUP: "/commercial/setup",
  COMMERCIAL_REVIEW: "/commercial/review",
  COMMERCIAL_RENEWALS: "/commercial/renewals",
  COMMERCIAL_MATTERS: "/commercial/matters",
  CORPORATE: "/corporate",
  CORPORATE_DEALS: "/corporate/deals",
  EMPLOYMENT: "/employment",
  EMPLOYMENT_SETUP: "/employment/setup",
  EMPLOYMENT_REVIEW: "/employment/review",
  EMPLOYMENT_LEAVES: "/employment/leaves",
  EMPLOYMENT_INVESTIGATIONS: "/employment/investigations",
  EMPLOYMENT_EXPANSIONS: "/employment/expansions",
  EMPLOYMENT_SETTINGS: "/employment/settings",
  SETTINGS: "/settings",
  ADMIN_RATINGS: "/admin/ratings",
  ADMIN_USERS: "/admin/users",
  ADMIN_CONVERSATIONS: "/admin/conversations",
  ADMIN_LOGS: "/admin/logs",
  ADMIN_SYSTEM: "/admin/system",
} as const;

// WebSocket URL — prefer NEXT_PUBLIC_WS_URL, then auto-detect from browser location
export function getWsUrl(): string {
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }
  if (typeof window !== "undefined") {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const port = window.location.port || (protocol === "wss:" ? "443" : "80");
    const host = `${window.location.hostname}:${port}`;
    return `${protocol}//${host}`;
  }
  return "ws://localhost:8080";
}

// Backend API URL (public, for direct links like API docs)
export const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
