import React from "react";
import { useAuth, useI18n, useUI } from "@/state/app";
import {
  Bot,
  FlaskConical,
  HelpCircle,
  Home,
  LayoutDashboard,
  LineChart,
  Settings as Cog,
  Sigma,
  TrendingUp,
  Mail,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";

export const Sidebar: React.FC = () => {
  const { user } = useAuth();
  const { t } = useI18n();
  const ui = useUI();

  const items = [
    { to: "/dashboard", icon: Home, label: t("nav.dashboard"), visible: true },
    {
      to: "/data",
      icon: TrendingUp,
      label: t("nav.dataIngest"),
      visible: true,
    },
    {
      to: "/data/charts",
      icon: LineChart,
      label: t("nav.dataCharts"),
      visible: true,
    },
    {
      to: "/data/analysis",
      icon: Sigma,
      label: t("nav.dataAnalysis"),
      visible: true,
    },
    {
      to: "/backtesting",
      icon: FlaskConical,
      label: t("nav.backtesting"),
      visible: user?.role !== "admin" ? true : true,
    },
    {
      to: "/bot",
      icon: Bot,
      label: t("nav.botModule"),
      visible: user?.role === "trader" || user?.role === "admin",
    },
    {
      to: "/invitations",
      icon: Mail,
      label: "Invitations",
      visible: user?.role === "admin",
    },
    { to: "/settings", icon: Cog, label: t("nav.settings"), visible: true },
    { to: "/help", icon: HelpCircle, label: t("nav.help"), visible: true },
  ];

  return (
    <aside
      className={cn(
        "fixed left-0 top-16 bottom-0 z-30 border-r border-sidebar-border/70 bg-gradient-to-b from-[#0a121f] via-[#090f1a] to-[#060910] text-sidebar-foreground shadow-[6px_0_18px_rgba(0,0,0,0.45)] transition-all duration-300",
        ui.sidebarCollapsed ? "w-16" : "w-64",
      )}
    >
      <div className="flex h-full flex-col">
        <nav className="px-3 pb-4 pt-5 space-y-1">
          {items
            .filter((i) => i.visible)
            .map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  cn(
                    "group relative flex items-center gap-3 overflow-hidden rounded-md px-3 py-2.5 text-[0.72rem] font-semibold uppercase tracking-[0.18em] transition-all",
                    isActive
                      ? "border border-primary/40 bg-primary/10 text-foreground shadow-inner"
                      : "border border-transparent text-muted-foreground/80 hover:border-primary/30 hover:bg-sidebar-accent/60 hover:text-foreground",
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <span
                      className={cn(
                        "pointer-events-none absolute left-2 top-1/2 h-7 w-[3px] -translate-y-1/2 rounded-full bg-primary/80 transition-opacity",
                        isActive
                          ? "opacity-100"
                          : "opacity-0 group-hover:opacity-50",
                      )}
                    />
                    <Icon
                      className={cn(
                        "size-5 flex-shrink-0 transition-colors",
                        isActive
                          ? "text-primary"
                          : "text-muted-foreground/70 group-hover:text-foreground",
                      )}
                    />
                    {!ui.sidebarCollapsed && (
                      <span className="truncate">{label}</span>
                    )}
                  </>
                )}
              </NavLink>
            ))}
          {user?.role === "admin" && (
            <>
              <NavLink
                to="/admin/users"
                className={({ isActive }) =>
                  cn(
                    "group relative mt-4 flex items-center gap-3 overflow-hidden rounded-md px-3 py-2.5 text-[0.72rem] font-semibold uppercase tracking-[0.18em] transition-all",
                    isActive
                      ? "border border-primary/40 bg-primary/10 text-foreground shadow-inner"
                      : "border border-transparent text-muted-foreground/80 hover:border-primary/30 hover:bg-sidebar-accent/60 hover:text-foreground",
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <span
                      className={cn(
                        "pointer-events-none absolute left-2 top-1/2 h-7 w-[3px] -translate-y-1/2 rounded-full bg-primary/80 transition-opacity",
                        isActive
                          ? "opacity-100"
                          : "opacity-0 group-hover:opacity-50",
                      )}
                    />
                    <LayoutDashboard
                      className={cn(
                        "size-5 flex-shrink-0 transition-colors",
                        isActive
                          ? "text-primary"
                          : "text-muted-foreground/70 group-hover:text-foreground",
                      )}
                    />
                    {!ui.sidebarCollapsed && (
                      <span>{t("nav.userManagement")}</span>
                    )}
                  </>
                )}
              </NavLink>
              <NavLink
                to="/admin/invitations"
                className={({ isActive }) =>
                  cn(
                    "group relative mt-1 flex items-center gap-3 overflow-hidden rounded-md px-3 py-2.5 text-[0.72rem] font-semibold uppercase tracking-[0.18em] transition-all",
                    isActive
                      ? "border border-primary/40 bg-primary/10 text-foreground shadow-inner"
                      : "border border-transparent text-muted-foreground/80 hover:border-primary/30 hover:bg-sidebar-accent/60 hover:text-foreground",
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <span
                      className={cn(
                        "pointer-events-none absolute left-2 top-1/2 h-7 w-[3px] -translate-y-1/2 rounded-full bg-primary/80 transition-opacity",
                        isActive
                          ? "opacity-100"
                          : "opacity-0 group-hover:opacity-50",
                      )}
                    />
                    <Mail
                      className={cn(
                        "size-5 flex-shrink-0 transition-colors",
                        isActive
                          ? "text-primary"
                          : "text-muted-foreground/70 group-hover:text-foreground",
                      )}
                    />
                    {!ui.sidebarCollapsed && <span>Invitations</span>}
                  </>
                )}
              </NavLink>
            </>
          )}
        </nav>
        {!ui.sidebarCollapsed && (
          <div className="mt-1 border-t border-border/40 px-3 pt-4">
            <div className="mb-2 text-[0.65rem] font-semibold uppercase tracking-[0.3em] text-muted-foreground/70">
              Conversations
            </div>
            <div className="max-h-64 space-y-2 overflow-auto pr-1 pb-2">
              {["Welcome", "Market Recap", "Strategy Idea"].map((title) => (
                <button
                  key={title}
                  className="w-full rounded-md border border-border/30 bg-gradient-to-r from-[#10192a] to-[#0d1524] px-3 py-2 text-left text-xs font-medium text-foreground/90 shadow-inner transition-all hover:border-primary/30 hover:text-foreground"
                >
                  <div className="truncate">{title}</div>
                  <div className="text-[0.65rem] uppercase tracking-[0.18em] text-muted-foreground/70">
                    Last message preview…
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
        <div className="mt-auto px-3 pb-4 pt-3">
          <button
            onClick={() => ui.setSidebarCollapsed(!ui.sidebarCollapsed)}
            className="w-full rounded-md border border-border/40 bg-gradient-to-r from-[#121b2d] to-[#0c131f] px-3 py-2 text-[0.68rem] font-semibold uppercase tracking-[0.3em] text-muted-foreground/80 transition-all hover:border-primary/40 hover:text-primary"
          >
            {ui.sidebarCollapsed ? "Expand" : "Collapse"}
          </button>
        </div>
      </div>
    </aside>
  );
};
