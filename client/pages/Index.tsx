import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth, useI18n } from "@/state/app";
import { useNavigate, Link } from "react-router-dom";

export default function Index() {
  const { login, isAuthenticated } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated) navigate("/dashboard", { replace: true });
  }, [isAuthenticated, navigate]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError(t("auth.invalidCredentials"));
      setLoading(false);
      return;
    }
    const res = await login(email, password, remember);
    setLoading(false);
    if (!res.ok) setError(res.message || t("auth.invalidCredentials"));
    else navigate("/dashboard");
  };

  return (
    <div className="relative flex min-h-screen flex-col bg-[radial-gradient(circle_at_top,_rgba(23,211,218,0.18),_transparent)] text-foreground">
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(140deg,rgba(8,13,23,0.95),rgba(5,9,16,0.92))]" aria-hidden />
      <div className="relative z-10 flex flex-1 items-center justify-center px-4 py-16">
        <div className="w-full max-w-md space-y-10">
          <div className="space-y-3 text-center">
            <div className="text-4xl font-black uppercase tracking-[0.4em] text-foreground/95">
              <span className="text-secondary">NQ</span>HUB
            </div>
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-muted-foreground/70">
              Professional Trading Platform
            </p>
          </div>
          <form
            onSubmit={onSubmit}
            className="space-y-6 rounded-3xl border border-border/40 bg-gradient-to-br from-[#131f32] via-[#0e1827] to-[#0a111d] p-8 shadow-[0_24px_48px_rgba(0,0,0,0.55)]"
          >
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email" className="text-xs font-semibold uppercase tracking-[0.26em] text-muted-foreground/70">
                  {t("auth.email")}
                </Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  required
                  className="rounded-full border border-border/40 bg-[#0c1624] px-4 py-3 text-sm text-muted-foreground/80 focus-visible:ring-primary"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password" className="text-xs font-semibold uppercase tracking-[0.26em] text-muted-foreground/70">
                  {t("auth.password")}
                </Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  minLength={8}
                  className="rounded-full border border-border/40 bg-[#0c1624] px-4 py-3 text-sm text-muted-foreground/80 focus-visible:ring-primary"
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-[0.7rem] uppercase tracking-[0.24em] text-muted-foreground/70">
              <label className="flex items-center gap-2 select-none">
                <input
                  type="checkbox"
                  className="size-4 rounded border border-border/60 bg-[#0c1624]"
                  style={{ accentColor: "hsl(var(--primary))" }}
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                />
                <span>{t("auth.rememberMe")}</span>
              </label>
              <Link
                to="/auth/forgot-password"
                className="text-primary transition-colors hover:text-primary/80"
              >
                {t("auth.forgotPassword")}
              </Link>
            </div>

            {error && (
              <div className="rounded-full border border-destructive/30 bg-destructive/15 px-4 py-2 text-center text-xs font-semibold uppercase tracking-[0.24em] text-destructive">
                {error}
              </div>
            )}

            <Button
              type="submit"
              className="h-11 w-full rounded-full border border-primary/40 bg-primary/20 text-xs font-semibold uppercase tracking-[0.32em] text-primary transition-colors hover:bg-primary/30"
              disabled={loading}
            >
              {loading ? "Signing in..." : t("auth.login")}
            </Button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border/30" />
              </div>
              <div className="relative flex justify-center text-[0.65rem] uppercase tracking-[0.26em] text-muted-foreground/70">
                <span className="bg-gradient-to-r from-[#131f32] via-[#0e1827] to-[#0a111d] px-3">or</span>
              </div>
            </div>

            <div className="text-center text-[0.68rem] uppercase tracking-[0.26em] text-muted-foreground/70">
              <Link to="/auth/request-access" className="transition-colors hover:text-foreground">
                {t("auth.requestAccess")}
              </Link>
            </div>
            <p className="text-center text-[0.6rem] uppercase tracking-[0.24em] text-muted-foreground/60">
              Demo: use emails like <code className="rounded bg-[#0d1625] px-2 py-1 text-primary">admin@</code>, <code className="rounded bg-[#0d1625] px-2 py-1 text-primary">trader@</code>, or <code className="rounded bg-[#0d1625] px-2 py-1 text-primary">senior@</code>
            </p>
          </form>
          <footer className="text-center text-[0.6rem] uppercase tracking-[0.32em] text-muted-foreground/60">
            <div className="flex items-center justify-center gap-4">
              <a href="#" className="transition-colors hover:text-foreground">Terms</a>
              <span className="text-border/60">•</span>
              <a href="#" className="transition-colors hover:text-foreground">Privacy</a>
              <span className="text-border/60">•</span>
              <a href="#" className="transition-colors hover:text-foreground">Contact</a>
            </div>
            <p className="mt-3">© 2024 NQHUB. All rights reserved.</p>
          </footer>
        </div>
      </div>
    </div>
  );
}
