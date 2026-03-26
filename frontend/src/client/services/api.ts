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

  // ==================== Generic HTTP Methods ====================

  async get<T = any>(url: string, config?: any): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T = any>(url: string, data?: any, config?: any): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  // ==================== ETL Endpoints ====================

  async analyzeZip(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post('/etl/analyze-zip', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  async uploadZip(file: File, selectedTimeframes?: string[]): Promise<import("@/types/etl").ETLJob> {
    const formData = new FormData();
    formData.append('file', file);

    if (selectedTimeframes && selectedTimeframes.length > 0) {
      formData.append('selected_timeframes', JSON.stringify(selectedTimeframes));
    }

    const response = await this.client.post<import("@/types/etl").ETLJob>('/etl/upload-zip', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  async getETLJobStatus(jobId: string): Promise<import("@/types/etl").ETLJob> {
    const response = await this.client.get<import("@/types/etl").ETLJob>(`/etl/jobs/${jobId}`);
    return response.data;
  }

  async listETLJobs(skip: number = 0, limit: number = 20, status?: string): Promise<import("@/types/etl").ETLJobList> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });

    if (status) {
      params.append('status', status);
    }

    const response = await this.client.get<import("@/types/etl").ETLJobList>(`/etl/jobs?${params}`);
    return response.data;
  }

  async cancelETLJob(jobId: string): Promise<void> {
    await this.client.delete(`/etl/jobs/${jobId}`);
  }

  // ==================== ETL Job Logs Methods (FASE 3) ====================

  async getETLJobLogs(
    jobId: string,
    skip: number = 0,
    limit: number = 100,
    level?: string
  ): Promise<import("@/types/etl").ETLJobLogList> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });

    if (level) {
      params.append('level', level);
    }

    const response = await this.client.get<import("@/types/etl").ETLJobLogList>(
      `/etl/jobs/${jobId}/logs?${params}`
    );
    return response.data;
  }

  // ==================== Worker Status Methods (FASE 5) ====================

  async getWorkerStatus(): Promise<import("@/types/etl").WorkerStatus> {
    const response = await this.client.get<import("@/types/etl").WorkerStatus>('/etl/worker/status');
    return response.data;
  }

  // ==================== Database Statistics Methods ====================

  async getDatabaseStatistics(): Promise<import("@/types/etl").DatabaseStatistics> {
    const response = await this.client.get<import("@/types/etl").DatabaseStatistics>('/etl/statistics');
    return response.data;
  }

  // ==================== Symbol Details Methods (FASE 1) ====================

  async getSymbolDetails(): Promise<import("@/types/etl").SymbolDetailsList> {
    const response = await this.client.get<import("@/types/etl").SymbolDetailsList>('/etl/symbols/details');
    return response.data;
  }

  // ==================== Coverage Heatmap Methods (FASE 1) ====================

  async getCoverageHeatmap(
    symbol?: string,
    startDate?: string,
    endDate?: string
  ): Promise<import("@/types/etl").CoverageHeatMapResponse> {
    const params = new URLSearchParams();

    if (symbol) params.append('symbol', symbol);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const queryString = params.toString();
    const url = queryString ? `/etl/coverage?${queryString}` : '/etl/coverage';

    const response = await this.client.get<import("@/types/etl").CoverageHeatMapResponse>(url);
    return response.data;
  }

  // ==================== Cleanup Methods (FASE 2) ====================

  async cleanupETLJobs(statusFilter: string = 'pending', olderThanHours: number = 24): Promise<{ deleted_count: number }> {
    const params = new URLSearchParams({
      status_filter: statusFilter,
      older_than_hours: olderThanHours.toString(),
    });

    const response = await this.client.delete<{ deleted_count: number; status_filter: string; older_than_hours: number }>(
      `/etl/jobs/cleanup?${params}`
    );
    return response.data;
  }

  // ==================== Pattern Detection ====================

  /**
   * Generate Fair Value Gaps for a date range
   */
  async generateFVGs(request: import("@/types/patterns").FVGDetectionRequest): Promise<import("@/types/patterns").FVGGenerationResponse> {
    const response = await this.client.post<import("@/types/patterns").FVGGenerationResponse>('/patterns/fvgs/generate', request);
    return response.data;
  }

  /**
   * List detected FVGs with optional filters
   */
  async listFVGs(filters?: {
    symbol: string;
    timeframe?: string;
    start_date?: string;
    end_date?: string;
    significance?: string;
    status?: string;
  }): Promise<import("@/types/patterns").FVGListResponse> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) params.append(key, value.toString());
      });
    }
    const response = await this.client.get<import("@/types/patterns").FVGListResponse>(`/patterns/fvgs/list?${params}`);
    return response.data;
  }

  /**
   * Generate Liquidity Pools for a specific date
   */
  async generateLiquidityPools(request: import("@/types/patterns").LiquidityPoolDetectionRequest): Promise<import("@/types/patterns").LiquidityPoolGenerationResponse> {
    const response = await this.client.post<import("@/types/patterns").LiquidityPoolGenerationResponse>('/patterns/liquidity-pools/generate', request);
    return response.data;
  }

  /**
   * List detected Liquidity Pools with optional filters
   */
  async listLiquidityPools(filters?: {
    symbol: string;
    timeframe?: string;
    start_date?: string;
    end_date?: string;
    pool_type?: string;
    strength?: string;
    status?: string;
  }): Promise<import("@/types/patterns").LiquidityPoolListResponse> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) params.append(key, value.toString());
      });
    }
    const response = await this.client.get<import("@/types/patterns").LiquidityPoolListResponse>(`/patterns/liquidity-pools/list?${params}`);
    return response.data;
  }

  /**
   * Generate Order Blocks for a date range
   */
  async generateOrderBlocks(request: import("@/types/patterns").OrderBlockDetectionRequest): Promise<import("@/types/patterns").OrderBlockGenerationResponse> {
    const response = await this.client.post<import("@/types/patterns").OrderBlockGenerationResponse>('/patterns/order-blocks/generate', request);
    return response.data;
  }

  /**
   * List detected Order Blocks with optional filters
   */
  async listOrderBlocks(filters?: {
    symbol: string;
    timeframe?: string;
    start_date?: string;
    end_date?: string;
    ob_type?: string;
    quality?: string;
    status?: string;
  }): Promise<import("@/types/patterns").OrderBlockListResponse> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) params.append(key, value.toString());
      });
    }
    const response = await this.client.get<import("@/types/patterns").OrderBlockListResponse>(`/patterns/order-blocks/list?${params}`);
    return response.data;
  }

  /**
   * Get interaction history for a specific pattern
   */
  async getPatternInteractions(
    patternType: "FVG" | "LP" | "OB",
    patternId: number,
    timeframe: string = "5min"
  ): Promise<import("@/types/patterns").PatternInteractionsResponse> {
    const response = await this.client.get<import("@/types/patterns").PatternInteractionsResponse>(
      `/patterns/patterns/${patternType}/${patternId}/interactions?timeframe=${timeframe}`
    );
    return response.data;
  }

  // ==================== Market State ====================

  /**
   * Generate market state snapshots for a time range
   */
  async generateMarketState(
    request: import("@/types/patterns").MarketStateGenerateRequest
  ): Promise<import("@/types/patterns").MarketStateGenerateResponse> {
    const response = await this.client.post<import("@/types/patterns").MarketStateGenerateResponse>(
      '/market-state/generate',
      request
    );
    return response.data;
  }

  /**
   * Get detailed market state with full pattern data for all 9 timeframes
   */
  async getMarketStateDetail(
    symbol: string,
    snapshot_time: string
  ): Promise<import("@/types/patterns").MarketStateDetailResponse> {
    const params = new URLSearchParams({
      symbol,
      snapshot_time
    });
    const response = await this.client.get<import("@/types/patterns").MarketStateDetailResponse>(
      `/market-state/detail?${params}`
    );
    return response.data;
  }

  /**
   * List available market state snapshots
   */
  async listMarketStateSnapshots(filters: {
    symbol: string;
    start_time?: string;
    end_time?: string;
    limit?: number;
  }): Promise<import("@/types/patterns").MarketStateListResponse> {
    const params = new URLSearchParams({ symbol: filters.symbol });
    if (filters.start_time) params.append('start_time', filters.start_time);
    if (filters.end_time) params.append('end_time', filters.end_time);
    if (filters.limit) params.append('limit', filters.limit.toString());

    const response = await this.client.get<import("@/types/patterns").MarketStateListResponse>(
      `/market-state/list?${params}`
    );
    return response.data;
  }

  /**
   * Get generation progress for a job
   */
  async getMarketStateProgress(
    job_id: string
  ): Promise<import("@/types/patterns").MarketStateProgressResponse> {
    const response = await this.client.get<import("@/types/patterns").MarketStateProgressResponse>(
      `/market-state/progress/${job_id}`
    );
    return response.data;
  }

  // ==================== Audit ====================

  /**
   * Generate Order Blocks audit report
   */
  async generateOrderBlocksAudit(
    request: import("@/types/audit").AuditOrderBlocksRequest
  ): Promise<import("@/types/audit").AuditOrderBlocksResponse> {
    const response = await this.client.post<import("@/types/audit").AuditOrderBlocksResponse>(
      `/audit/order-blocks`,
      request
    );
    return response.data;
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
