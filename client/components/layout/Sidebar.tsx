import React from "react";
import { useAuth, useI18n, useUI } from "@/state/app";
import { Bot, FlaskConical, HelpCircle, Home, LayoutDashboard, Settings as Cog, TrendingUp } from "lucide-react";
import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";

export const Sidebar: React.FC = () => {
  const { user } = useAuth();
  const { t } = useI18n();
  const ui = useUI();

  const items = [
    { to: "/dashboard", icon: Home, label: t("nav.dashboard"), visible: true },
    { to: "/data", icon: TrendingUp, label: t("nav.dataModule"), visible: true },
    { to: "/backtesting", icon: FlaskConical, label: t("nav.backtesting"), visible: user?.role !== "admin" ? true : true },
    { to: "/bot", icon: Bot, label: t("nav.botModule"), visible: user?.role === "trader" || user?.role === "admin" },
    { to: "/settings", icon: Cog, label: t("nav.settings"), visible: true },
    { to: "/help", icon: HelpCircle, label: t("nav.help"), visible: true },
  ];

  return (
    <aside className={cn("fixed left-0 top-16 bottom-0 border-r border-sidebar-border bg-sidebar text-sidebar-foreground z-30 transition-all duration-300", ui.sidebarCollapsed ? "w-14" : "w-60")}>
      <div className="h-full flex flex-col">
        <nav className="py-2 space-y-1 px-2">
          {items.filter(i => i.visible).map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} className={({ isActive }) => cn("flex items-center gap-3 px-3 py-2.5 text-sm rounded-md transition-colors", isActive ? "bg-sidebar-primary text-sidebar-primary-foreground" : "hover:bg-sidebar-accent text-sidebar-foreground") }>
              <Icon className="size-5 flex-shrink-0" />
              {!ui.sidebarCollapsed && <span className="truncate">{label}</span>}
            </NavLink>
          ))}
          {user?.role === "admin" && (
            <NavLink to="/admin/users" className={({ isActive }) => cn("mt-2 flex items-center gap-3 px-3 py-2.5 text-sm rounded-md transition-colors", isActive ? "bg-sidebar-primary text-sidebar-primary-foreground" : "hover:bg-sidebar-accent text-sidebar-foreground")}>
              <LayoutDashboard className="size-5 flex-shrink-0" />
              {!ui.sidebarCollapsed && <span>{t("nav.userManagement")}</span>}
            </NavLink>
          )}
        </nav>
        {!ui.sidebarCollapsed && (
          <div className="mt-1 pt-2 border-t border-border/60">
            <div className="px-3 text-xs font-semibold text-muted-foreground mb-1">Conversations</div>
            <div className="max-h-64 overflow-auto pb-1">
              {["Welcome", "Market recap", "Strategy idea"].map((t) => (
                <button key={t} className="w-full text-left px-3 py-2 text-sm rounded hover:bg-sidebar-accent">
                  <div className="font-medium truncate">{t}</div>
                  <div className="text-xs text-muted-foreground truncate">Last message preview…</div>
                </button>
              ))}
            </div>
          </div>
        )}
        <div className="mt-auto">
          <button onClick={() => ui.setSidebarCollapsed(!ui.sidebarCollapsed)} className="m-3 px-3 py-2 text-xs rounded bg-sidebar-accent hover:opacity-90">{ui.sidebarCollapsed ? ">>" : "<<"}</button>
        </div>
      </div>
    </aside>
  );
};
