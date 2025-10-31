import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth, useI18n } from "@/state/app";
import { useNavigate, Link } from "react-router-dom";

export default function Register() {
  const { register, isAuthenticated } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [invitationToken, setInvitationToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check if invitation token is in URL params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (token) {
      setInvitationToken(token);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) navigate("/dashboard", { replace: true });
  }, [isAuthenticated, navigate]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Validation
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError("Invalid email format");
      setLoading(false);
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      setLoading(false);
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      setLoading(false);
      return;
    }

    if (!invitationToken) {
      setError("Invitation token is required");
      setLoading(false);
      return;
    }

    const res = await register({
      email,
      password,
      full_name: fullName || undefined,
      invitation_token: invitationToken,
    });

    setLoading(false);

    if (!res.ok) {
      setError(res.message || "Registration failed");
    } else {
      navigate("/dashboard");
    }
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
              Register New Account
            </p>
          </div>
          <form
            onSubmit={onSubmit}
            className="space-y-6 rounded-3xl border border-border/40 bg-gradient-to-br from-[#131f32] via-[#0e1827] to-[#0a111d] p-8 shadow-[0_24px_48px_rgba(0,0,0,0.55)]"
          >
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="invitationToken" className="text-xs font-semibold uppercase tracking-[0.26em] text-muted-foreground/70">
                  Invitation Token *
                </Label>
                <Input
                  id="invitationToken"
                  type="text"
                  value={invitationToken}
                  onChange={(e) => setInvitationToken(e.target.value)}
                  placeholder="Enter your invitation token"
                  required
                  className="rounded-full border border-border/40 bg-[#0c1624] px-4 py-3 text-sm text-muted-foreground/80 focus-visible:ring-primary"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email" className="text-xs font-semibold uppercase tracking-[0.26em] text-muted-foreground/70">
                  {t("auth.email")} *
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
                <Label htmlFor="fullName" className="text-xs font-semibold uppercase tracking-[0.26em] text-muted-foreground/70">
                  Full Name
                </Label>
                <Input
                  id="fullName"
                  type="text"
                  autoComplete="name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Your full name (optional)"
                  className="rounded-full border border-border/40 bg-[#0c1624] px-4 py-3 text-sm text-muted-foreground/80 focus-visible:ring-primary"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="text-xs font-semibold uppercase tracking-[0.26em] text-muted-foreground/70">
                  {t("auth.password")} *
                </Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  minLength={8}
                  className="rounded-full border border-border/40 bg-[#0c1624] px-4 py-3 text-sm text-muted-foreground/80 focus-visible:ring-primary"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword" className="text-xs font-semibold uppercase tracking-[0.26em] text-muted-foreground/70">
                  Confirm Password *
                </Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  minLength={8}
                  className="rounded-full border border-border/40 bg-[#0c1624] px-4 py-3 text-sm text-muted-foreground/80 focus-visible:ring-primary"
                />
              </div>
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
              {loading ? "Registering..." : "Register"}
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
              <Link to="/" className="transition-colors hover:text-foreground">
                Already have an account? {t("auth.login")}
              </Link>
            </div>
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
