/**
 * Authentication types.
 */

export interface User {
  id: string;
  email: string;
  name?: string;
  is_active: boolean;
  role?: string;
  created_at: string;
  avatar_url?: string | null;
  llm_provider?: string | null;
  ai_model?: string | null;
  llm_base_url?: string | null;
  has_openai_key?: boolean;
  has_anthropic_key?: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name?: string;
}

export interface RegisterResponse {
  id: string;
  email: string;
  name?: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
  refresh_token?: string;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
