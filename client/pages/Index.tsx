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
          <div className="text-center mb-6">
            <div className="text-3xl font-extrabold tracking-tight"><span className="text-primary">NQ</span>HUB</div>
            <p className="mt-2 text-sm text-muted-foreground">Secure sign-in</p>
          </div>
          <form onSubmit={onSubmit} className="bg-card border border-border/60 rounded-lg p-6 shadow-md">
            <div className="space-y-4">
              <div>
                <Label htmlFor="email">{t("auth.email")}</Label>
                <Input id="email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </div>
              <div>
                <Label htmlFor="password">{t("auth.password")}</Label>
                <Input id="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
              </div>
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm select-none">
                  <input type="checkbox" className="accent-primary" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
                  {t("auth.rememberMe")}
                </label>
                <Link to="/auth/forgot-password" className="text-sm text-primary hover:underline">{t("auth.forgotPassword")}</Link>
              </div>
              {error && <div className="text-sm text-destructive">{error}</div>}
              <Button type="submit" className="w-full" disabled={loading}>{loading ? "Signing in..." : t("auth.login")}</Button>
            </div>
            <div className="mt-4 text-center">
              <Link to="/auth/request-access" className="text-sm text-muted-foreground hover:text-foreground underline">{t("auth.requestAccess")}</Link>
            </div>
            <p className="mt-4 text-xs text-muted-foreground">
              Tip: use an email like admin@ to login as admin, or trader@ / senior@ / junior@ for other roles.
            </p>
          </form>
          <footer className="mt-6 text-center text-xs text-muted-foreground">
            <a href="#" className="hover:underline">Terms</a> • <a href="#" className="hover:underline">Privacy</a> • <a href="#" className="hover:underline">Contact</a>
          </footer>
        </div>
      </div>
    </div>
  );
}
