/**
 * API Service
 * Axios client with JWT interceptors for backend communication
 */

import axios, { AxiosError, AxiosInstance } from "axios";
import type {
  User,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  RefreshRequest,
  Invitation,
  InvitationCreate,
  ApiError,
} from "@/types/auth";

// API base URL - uses Vite proxy in development
const API_BASE_URL = "/api/v1";

// Token storage keys
const ACCESS_TOKEN_KEY = "nqhub_access_token";
const REFRESH_TOKEN_KEY = "nqhub_refresh_token";

class ApiClient {
  private client: AxiosInstance;
  private refreshing: Promise<string | null> | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor - Add Bearer token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - Handle 401 and refresh token
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<ApiError>) => {
        const originalRequest = error.config;

        // If 401 and we have a refresh token, try to refresh
        if (error.response?.status === 401 && originalRequest && !originalRequest.headers?.["X-Retry"]) {
          const refreshToken = this.getRefreshToken();

          if (refreshToken) {
            try {
              // Prevent multiple refresh calls
              if (!this.refreshing) {
                this.refreshing = this.refreshAccessToken(refreshToken);
              }

              const newAccessToken = await this.refreshing;
              this.refreshing = null;

              if (newAccessToken) {
                // Retry original request with new token
                if (!originalRequest.headers) {
                  originalRequest.headers = {} as any;
                }
                originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                originalRequest.headers["X-Retry"] = "true";
                return this.client(originalRequest);
              }
            } catch (refreshError) {
              // Refresh failed, clear tokens and reject
              this.clearTokens();
              this.refreshing = null;
              return Promise.reject(refreshError);
            }
          } else {
            // No refresh token, clear and reject
            this.clearTokens();
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // ==================== Token Management ====================

  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }

  clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  // ==================== Auth Endpoints ====================

  async login(data: LoginRequest): Promise<TokenResponse> {
    const response = await this.client.post<TokenResponse>("/auth/login", data);
    this.setTokens(response.data.access_token, response.data.refresh_token);
    return response.data;
  }

  async register(data: RegisterRequest): Promise<TokenResponse> {
    const response = await this.client.post<TokenResponse>("/auth/register", data);
    this.setTokens(response.data.access_token, response.data.refresh_token);
    return response.data;
  }

  async refreshAccessToken(refreshToken: string): Promise<string | null> {
    try {
      const response = await this.client.post<TokenResponse>("/auth/refresh", {
        refresh_token: refreshToken,
      } as RefreshRequest);

      this.setTokens(response.data.access_token, response.data.refresh_token);
      return response.data.access_token;
    } catch (error) {
      this.clearTokens();
      return null;
    }
  }

  async getMe(): Promise<User> {
    const response = await this.client.get<User>("/auth/me");
    return response.data;
  }

  logout(): void {
    this.clearTokens();
  }

  async forgotPassword(email: string): Promise<void> {
    await this.client.post("/auth/forgot-password", { email });
  }

  async resetPassword(token: string, newPassword: string): Promise<void> {
    await this.client.post("/auth/reset-password", {
      token,
      new_password: newPassword,
    });
  }

  // ==================== Invitations Endpoints (Superuser only) ====================

  async createInvitation(data: InvitationCreate): Promise<Invitation> {
    const response = await this.client.post<Invitation>("/invitations", data);
    return response.data;
  }

  async getInvitations(): Promise<Invitation[]> {
    const response = await this.client.get<Invitation[]>("/invitations");
    return response.data;
  }

  async deleteInvitation(id: number): Promise<void> {
    await this.client.delete(`/invitations/${id}`);
  }

  // ==================== Error Handling Helpers ====================

  static isApiError(error: unknown): error is AxiosError<ApiError> {
    return axios.isAxiosError(error);
  }

  static getErrorMessage(error: unknown): string {
    if (this.isApiError(error)) {
      return error.response?.data?.detail || error.message || "An error occurred";
    }
    if (error instanceof Error) {
      return error.message;
    }
    return "An unknown error occurred";
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export class for testing
export { ApiClient };
