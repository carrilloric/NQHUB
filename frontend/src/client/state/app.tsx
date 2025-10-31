import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { apiClient, ApiClient } from "@/services/api";
import type { User as ApiUser, LoginRequest, RegisterRequest } from "@/types/auth";

// Legacy role mapping for backward compatibility
export type Role = "admin" | "trader" | "analystSenior" | "analystJunior";

// Extended user with legacy role mapping
export interface User extends Omit<ApiUser, "role"> {
  role: Role;
  firstName: string;
  lastName: string;
}

// Map backend roles to frontend roles
function mapBackendRole(backendRole: "superuser" | "trader"): Role {
  switch (backendRole) {
    case "superuser":
      return "admin";
    case "trader":
      return "trader";
    default:
      return "trader";
  }
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, remember?: boolean) => Promise<{ ok: boolean; message?: string }>;
  register: (data: RegisterRequest) => Promise<{ ok: boolean; message?: string }>;
  logout: () => void;
}

interface UIState {
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (v: boolean) => void;
  llmPanelOpen: boolean;
  setLlmPanelOpen: (v: boolean) => void;
  llmPanelHeight: number; // px
  setLlmPanelHeight: (h: number) => void;
  theme: "dark" | "light";
  setTheme: (t: "dark" | "light") => void;
  language: "en" | "es";
  setLanguage: (l: "en" | "es") => void;
  pendingRequests: number; // admin badge
  setPendingRequests: (n: number) => void;
}

interface I18n {
  t: (key: string) => string;
}

const AuthContext = createContext<AuthState | null>(null);
const UIContext = createContext<UIState | null>(null);
const I18nContext = createContext<I18n | null>(null);

function useLocalStorage<T>(key: string, initial: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      const raw = localStorage.getItem(key);
      return raw ? (JSON.parse(raw) as T) : initial;
    } catch {
      return initial;
    }
  });
  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {}
  }, [key, value]);
  return [value, setValue] as const;
}

export const AppProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const [sidebarCollapsed, setSidebarCollapsed] = useLocalStorage<boolean>("ui.sidebarCollapsed", true);
  const [llmPanelOpen, setLlmPanelOpen] = useLocalStorage<boolean>("ui.llmPanelOpen", false);
  const [llmPanelHeight, setLlmPanelHeight] = useLocalStorage<number>("ui.llmPanelHeight", 320);
  const [theme, setThemeState] = useLocalStorage<"dark" | "light">("theme", "light");
  const [language, setLanguage] = useLocalStorage<"en" | "es">("language", "en");
  const [pendingRequests, setPendingRequests] = useState<number>(3);

  // Helper to transform API user to frontend user
  const transformUser = useCallback((apiUser: ApiUser): User => {
    const [firstName, ...lastNameParts] = (apiUser.full_name || apiUser.email.split("@")[0]).split(" ");
    return {
      ...apiUser,
      role: mapBackendRole(apiUser.role),
      firstName: firstName || "User",
      lastName: lastNameParts.join(" ") || "",
    };
  }, []);

  const setTheme = useCallback((t: "dark" | "light") => {
    setThemeState(t);
    try {
      const root = document.documentElement;
      if (t === "dark") root.classList.add("dark");
      else root.classList.remove("dark");
      localStorage.setItem("theme", t);
    } catch {}
  }, [setThemeState]);

  useEffect(() => {
    setTheme(theme);
  }, []); // eslint-disable-line

  // Load user on mount if token exists
  useEffect(() => {
    const loadUser = async () => {
      const token = apiClient.getAccessToken();
      if (token) {
        try {
          const apiUser = await apiClient.getMe();
          setUser(transformUser(apiUser));
        } catch (error) {
          // Token invalid or expired, clear it
          apiClient.clearTokens();
        }
      }
      setIsLoading(false);
    };

    loadUser();
  }, [transformUser]);

  const login = useCallback<AuthState["login"]>(
    async (email, password, remember) => {
      try {
        if (!email || !password) {
          return { ok: false, message: "Missing credentials" };
        }

        await apiClient.login({ email, password });
        const apiUser = await apiClient.getMe();
        setUser(transformUser(apiUser));

        if (remember) {
          localStorage.setItem("rememberedEmail", email);
        }

        return { ok: true };
      } catch (error) {
        const message = ApiClient.getErrorMessage(error);
        return { ok: false, message };
      }
    },
    [transformUser]
  );

  const register = useCallback<AuthState["register"]>(
    async (data) => {
      try {
        await apiClient.register(data);
        const apiUser = await apiClient.getMe();
        setUser(transformUser(apiUser));
        return { ok: true };
      } catch (error) {
        const message = ApiClient.getErrorMessage(error);
        return { ok: false, message };
      }
    },
    [transformUser]
  );

  const logout = useCallback(() => {
    apiClient.logout();
    setUser(null);
  }, []);

  const auth = useMemo<AuthState>(
    () => ({ user, isAuthenticated: !!user, isLoading, login, register, logout }),
    [user, isLoading, login, register, logout]
  );

  const ui = useMemo<UIState>(() => ({
    sidebarCollapsed,
    setSidebarCollapsed,
    llmPanelOpen,
    setLlmPanelOpen,
    llmPanelHeight,
    setLlmPanelHeight,
    theme,
    setTheme,
    language,
    setLanguage,
    pendingRequests,
    setPendingRequests,
  }), [sidebarCollapsed, setSidebarCollapsed, llmPanelOpen, setLlmPanelOpen, llmPanelHeight, setLlmPanelHeight, theme, setTheme, language, setLanguage, pendingRequests]);

  const [dict, setDict] = useState<Record<string, string>>({});
  useEffect(() => {
    (async () => {
      const mod = await import(`@/locales/${language}.json`);
      setDict(mod.default as Record<string, string>);
    })();
  }, [language]);

  const t = useCallback((key: string) => {
    if (dict[key]) return dict[key];
    return key.split(".").reduce((acc, part) => (acc && typeof acc === "object" ? (acc as any)[part] : undefined), dict as any) || key;
  }, [dict]);

  const i18n = useMemo<I18n>(() => ({ t }), [t]);

  return (
    <AuthContext.Provider value={auth}>
      <UIContext.Provider value={ui}>
        <I18nContext.Provider value={i18n}>{children}</I18nContext.Provider>
      </UIContext.Provider>
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AppProvider");
  return ctx;
};
export const useUI = () => {
  const ctx = useContext(UIContext);
  if (!ctx) throw new Error("useUI must be used within AppProvider");
  return ctx;
};
export const useI18n = () => {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within AppProvider");
  return ctx;
};
