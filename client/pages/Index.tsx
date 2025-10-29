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
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <div className="flex-1 grid place-items-center p-6">
        <div className="w-full max-w-md">
          <div className="text-center mb-8 space-y-2">
            <div className="text-4xl font-extrabold tracking-tighter"><span className="text-primary">NQ</span>HUB</div>
            <p className="text-sm text-muted-foreground">Professional Trading Platform</p>
          </div>
          <form onSubmit={onSubmit} className="bg-card border border-border/40 rounded-lg p-6 shadow-lg space-y-5">
            <div>
              <Label htmlFor="email" className="text-sm font-medium">{t("auth.email")}</Label>
              <Input id="email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="your@email.com" required className="mt-1.5" />
            </div>
            <div>
              <Label htmlFor="password" className="text-sm font-medium">{t("auth.password")}</Label>
              <Input id="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required minLength={8} className="mt-1.5" />
            </div>
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm select-none cursor-pointer">
                <input type="checkbox" className="accent-primary cursor-pointer" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
                <span>{t("auth.rememberMe")}</span>
              </label>
              <Link to="/auth/forgot-password" className="text-sm text-primary hover:text-primary/80 transition-colors">{t("auth.forgotPassword")}</Link>
            </div>
            {error && <div className="text-sm text-destructive bg-destructive/10 border border-destructive/30 rounded px-3 py-2">{error}</div>}
            <Button type="submit" className="w-full h-10 font-medium" disabled={loading}>{loading ? "Signing in..." : t("auth.login")}</Button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border/30"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-card text-muted-foreground">or</span>
              </div>
            </div>

            <div className="text-center">
              <Link to="/auth/request-access" className="text-sm text-muted-foreground hover:text-foreground transition-colors">{t("auth.requestAccess")}</Link>
            </div>
            <p className="text-xs text-muted-foreground text-center">
              Demo: Use emails like <code className="bg-muted px-1.5 py-0.5 rounded">admin@</code>, <code className="bg-muted px-1.5 py-0.5 rounded">trader@</code>, or <code className="bg-muted px-1.5 py-0.5 rounded">senior@</code>
            </p>
          </form>
          <footer className="mt-8 pt-6 border-t border-border/30 text-center text-xs text-muted-foreground space-y-2">
            <div className="flex items-center justify-center gap-4">
              <a href="#" className="hover:text-foreground transition-colors">Terms</a>
              <span className="text-border/60">•</span>
              <a href="#" className="hover:text-foreground transition-colors">Privacy</a>
              <span className="text-border/60">•</span>
              <a href="#" className="hover:text-foreground transition-colors">Contact</a>
            </div>
            <p>© 2024 NQHUB. All rights reserved.</p>
          </footer>
        </div>
      </div>
    </div>
  );
}
