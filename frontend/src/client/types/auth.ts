/**
 * Authentication Types
 * These types match the backend API schema
 */

export type UserRole = "superuser" | "trader";

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
  invitation_token: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface Invitation {
  id: number;
  token: string;
  email: string | null;
  role: UserRole;
  created_at: string;
  expires_at: string;
  used_at: string | null;
  created_by_id: number | null;
  used_by_id: number | null;
}

export interface InvitationCreate {
  email?: string;
  role: UserRole;
  expires_in_days?: number;
}

export interface ApiError {
  detail: string;
}
