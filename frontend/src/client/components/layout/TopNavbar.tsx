import React from "react";
import { Slot } from "@radix-ui/react-slot";
import { useAuth, useI18n, useUI } from "@/state/app";
import { Bell, ChevronDown, Globe, Languages, LogOut, Moon, Settings, Sun, User } from "lucide-react";
import { cn } from "@/lib/utils";

export const TopNavbar: React.FC = () => {
  const { user, logout } = useAuth();
  const { t } = useI18n();
  const ui = useUI();

  const toggleTheme = () => ui.setTheme(ui.theme === "dark" ? "light" : "dark");

  const changeLang = () => ui.setLanguage(ui.language === "en" ? "es" : "en");

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-gradient-to-r from-[#121a2b] via-[#0d141f] to-[#121a2b] text-foreground/95 shadow-[0_2px_18px_rgba(0,0,0,0.55)] border-b border-primary/40 z-40">
      <div className="h-full flex items-center justify-between px-4 md:px-6">
        <div className="flex items-center gap-3">
          <div className="flex items-baseline gap-1 text-2xl font-black tracking-[0.32em] uppercase text-foreground">
            <span className="text-secondary">NQ</span>
            <span>Hub</span>
          </div>
          <span className="hidden lg:inline-block text-xs font-medium uppercase tracking-[0.32em] text-muted-foreground/80">
            {user ? t("dashboard.title") : t("auth.login")}
          </span>
        </div>

        <div className="hidden md:flex flex-1 items-center justify-center">
          <Ticker />
        </div>

        <div className="flex items-center gap-2">
          <ToolbarIcon onClick={() => ui.setLlmPanelOpen(!ui.llmPanelOpen)} aria-label="Toggle LLM">
            <Globe className="size-4" />
          </ToolbarIcon>
          <ToolbarIcon onClick={toggleTheme} aria-label="Toggle Theme">
            {ui.theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </ToolbarIcon>
          <ToolbarIcon onClick={changeLang} aria-label="Change Language">
            <Languages className="size-4" />
          </ToolbarIcon>
          <div className="relative">
            <ToolbarIcon aria-label="Notifications">
              <Bell className="size-4" />
            </ToolbarIcon>
            {user?.role === "admin" && ui.pendingRequests > 0 && (
              <span className="absolute -top-1 -right-1 bg-secondary text-secondary-foreground text-[10px] font-bold px-1.5 py-0.5 rounded-full shadow-sm">
                {ui.pendingRequests}
              </span>
            )}
          </div>
          {user && (
            <div className="hidden md:flex items-center pl-3 ml-3 border-l border-border/40">
              <div className="flex flex-col mr-3">
                <span className="text-sm font-semibold leading-5">{user.firstName || user.email}</span>
                <span className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">{user.role}</span>
              </div>
              <ToolbarIcon asChild aria-label="User Menu">
                <button className="flex items-center gap-1">
                  <User className="size-4" />
                  <ChevronDown className="size-4" />
                </button>
              </ToolbarIcon>
              <ToolbarIcon asChild className="ml-1" aria-label="Logout" onClick={logout}>
                <button className="flex items-center gap-1 text-sm font-semibold">
                  <LogOut className="size-4" />
                  {t("auth.logout")}
                </button>
              </ToolbarIcon>
              <ToolbarIcon className="ml-1" aria-label="Settings">
                <Settings className="size-4" />
              </ToolbarIcon>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

interface ToolbarIconProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
}

const ToolbarIcon = React.forwardRef<HTMLButtonElement, ToolbarIconProps>(
  ({ className, children, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        ref={ref}
        className={cn(
          "relative inline-flex h-9 min-w-[2.25rem] items-center justify-center rounded-full border border-border/30 bg-transparent text-muted-foreground/80 transition-all hover:border-primary/70 hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0d141f]",
          className,
        )}
        type={asChild ? undefined : "button"}
        {...props}
      >
        {children}
      </Comp>
    );
  },
);
ToolbarIcon.displayName = "ToolbarIcon";

const Ticker: React.FC = () => {
  return (
    <div
      className={cn(
        "flex items-center gap-4 rounded-full border border-primary/40 bg-gradient-to-r from-[#0b141f] to-[#0e1b28] px-5 py-2 text-xs font-medium uppercase tracking-[0.3em] text-muted-foreground/80 shadow-[0_0_24px_rgba(0,171,196,0.12)]",
      )}
    >
      <span className="text-secondary text-sm font-bold tracking-[0.26em]">NQ</span>
      <span className="tabular-nums text-base font-semibold text-foreground">15,234.12</span>
      <span className="text-bullish tabular-nums font-semibold">+0.85%</span>
      <div className="ml-2 flex h-2 w-24 items-center overflow-hidden rounded-full bg-muted/60">
        <div className="h-full w-1/2 bg-primary/70 animate-[pulse_1.8s_ease-in-out_infinite]"></div>
      </div>
    </div>
  );
};
