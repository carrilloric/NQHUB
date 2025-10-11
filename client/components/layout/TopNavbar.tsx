import React from "react";
import { useAuth, useI18n, useUI } from "@/state/app";
import { Bell, ChevronDown, Globe, Languages, LogOut, Moon, Settings, Sun, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const TopNavbar: React.FC = () => {
  const { user, logout } = useAuth();
  const { t } = useI18n();
  const ui = useUI();

  const toggleTheme = () => ui.setTheme(ui.theme === "dark" ? "light" : "dark");

  const changeLang = () => ui.setLanguage(ui.language === "en" ? "es" : "en");

  return (
    <header className="fixed top-0 left-0 right-0 h-16 border-b border-border/60 bg-sidebar text-sidebar-foreground z-40">
      <div className="h-full flex items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <div className="text-xl font-extrabold tracking-tight"><span className="text-primary">NQ</span>HUB</div>
          <span className="hidden md:inline-block text-sm text-muted-foreground">{user ? t("dashboard.title") : t("auth.login")}</span>
        </div>

        <div className="flex-1 flex items-center justify-center">
          <Ticker />
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" aria-label="Toggle LLM" onClick={() => ui.setLlmPanelOpen(!ui.llmPanelOpen)}>
            <Globe className="size-5" />
          </Button>
          <Button variant="ghost" size="icon" aria-label="Toggle Theme" onClick={toggleTheme}>
            {ui.theme === "dark" ? <Sun className="size-5" /> : <Moon className="size-5" />}
          </Button>
          <Button variant="ghost" size="icon" aria-label="Change Language" onClick={changeLang}>
            <Languages className="size-5" />
          </Button>
          <div className="relative">
            <Button variant="ghost" size="icon" aria-label="Notifications">
              <Bell className="size-5" />
            </Button>
            {user?.role === "admin" && ui.pendingRequests > 0 && (
              <span className="absolute -top-1 -right-1 bg-primary text-primary-foreground text-[10px] font-bold px-1.5 py-0.5 rounded">{ui.pendingRequests}</span>
            )}
          </div>
          {user && (
            <div className="flex items-center pl-2 ml-2 border-l border-border/60">
              <User className="mr-2 size-5 text-muted-foreground" />
              <div className="mr-2 text-sm">
                <div className="leading-4 font-medium">{user.firstName || user.email}</div>
                <div className="text-xs text-muted-foreground capitalize">{user.role}</div>
              </div>
              <ChevronDown className="size-4 text-muted-foreground" />
              <Button variant="ghost" className="ml-2" size="sm" onClick={logout}>
                <LogOut className="size-4 mr-1" /> {t("auth.logout")}
              </Button>
              <Button variant="ghost" size="icon" className="ml-1" aria-label="Settings">
                <Settings className="size-5" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

const Ticker: React.FC = () => {
  return (
    <div className={cn("px-3 py-1 rounded-md border border-border/60 bg-card text-card-foreground text-sm flex items-center gap-3")}> 
      <span className="font-semibold">NQ</span>
      <span className="tabular-nums">15,234.12</span>
      <span className="text-green-400">+0.85%</span>
      <div className="ml-3 h-1 w-20 bg-muted rounded overflow-hidden">
        <div className="h-full w-1/2 bg-primary animate-pulse"></div>
      </div>
    </div>
  );
};
