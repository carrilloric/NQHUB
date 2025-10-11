import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

export type Role = "admin" | "trader" | "analystSenior" | "analystJunior";

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: Role;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string, remember?: boolean) => Promise<{ ok: boolean; message?: string }>;
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

  const [sidebarCollapsed, setSidebarCollapsed] = useLocalStorage<boolean>("ui.sidebarCollapsed", true);
  const [llmPanelOpen, setLlmPanelOpen] = useLocalStorage<boolean>("ui.llmPanelOpen", false);
  const [llmPanelHeight, setLlmPanelHeight] = useLocalStorage<number>("ui.llmPanelHeight", 320);
  const [theme, setThemeState] = useLocalStorage<"dark" | "light">("theme", "light");
  const [language, setLanguage] = useLocalStorage<"en" | "es">("language", "en");
  const [pendingRequests, setPendingRequests] = useState<number>(3);

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

  const login = useCallback<AuthState["login"]>(async (email, password, remember) => {
    await new Promise((r) => setTimeout(r, 400));
    if (!email || !password) return { ok: false, message: "Missing credentials" };
    let role: Role = "trader";
    if (email.toLowerCase().includes("admin")) role = "admin";
    else if (email.toLowerCase().includes("senior")) role = "analystSenior";
    else if (email.toLowerCase().includes("junior")) role = "analystJunior";
    const newUser: User = {
      id: "u_" + Math.random().toString(36).slice(2),
      email,
      firstName: "User",
      lastName: "",
      role,
    };
    setUser(newUser);
    if (remember) localStorage.setItem("rememberedEmail", email);
    return { ok: true };
  }, []);

  const logout = useCallback(() => {
    setUser(null);
  }, []);

  const auth = useMemo<AuthState>(() => ({ user, isAuthenticated: !!user, login, logout }), [user, login, logout]);

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
