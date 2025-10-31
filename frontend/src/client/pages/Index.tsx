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
    <div className="min-h-screen bg-[#0a1628] flex items-center justify-center px-4">
      <div className="w-full max-w-md space-y-8">
        {/* Logo */}
        <div className="text-center space-y-2">
          <h1 className="text-5xl font-bold tracking-[0.2em]">
            <span className="text-[#e8b44d]">NQ</span>
            <span className="text-white">HUB</span>
          </h1>
          <p className="text-[#6b7c93] text-xs uppercase tracking-[0.3em]">
            Professional Trading Platform
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-[#0f1f3a] rounded-2xl p-8 shadow-2xl border border-[#1a2d4a]">
          <form onSubmit={onSubmit} className="space-y-6">
            {/* Email Field */}
            <div className="space-y-2">
              <Label htmlFor="email" className="text-[#6b7c93] text-xs uppercase tracking-wider">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                className="bg-[#0a1628] border-[#1a2d4a] text-white placeholder:text-[#4a5a72] focus:border-[#2dd4bf] focus:ring-[#2dd4bf]"
              />
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <Label htmlFor="password" className="text-[#6b7c93] text-xs uppercase tracking-wider">
                Password
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
                className="bg-[#0a1628] border-[#1a2d4a] text-white placeholder:text-[#4a5a72] focus:border-[#2dd4bf] focus:ring-[#2dd4bf]"
              />
            </div>

            {/* Remember Me & Forgot Password */}
            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 text-[#6b7c93] cursor-pointer">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded border-[#1a2d4a] bg-[#0a1628] text-[#2dd4bf] focus:ring-[#2dd4bf]"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                />
                <span className="text-xs uppercase tracking-wide">Remember me</span>
              </label>
              <Link
                to="/auth/forgot-password"
                className="text-[#2dd4bf] hover:text-[#34e4cb] text-xs uppercase tracking-wide transition-colors"
              >
                Forgot Password?
              </Link>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-2 rounded-lg text-sm text-center">
                {error}
              </div>
            )}

            {/* Login Button */}
            <Button
              type="submit"
              className="w-full bg-[#2dd4bf] hover:bg-[#34e4cb] text-[#0a1628] font-semibold uppercase tracking-wide py-6 rounded-full transition-colors"
              disabled={loading}
            >
              {loading ? "Signing in..." : "Login"}
            </Button>

            {/* Divider */}
            <div className="relative py-3">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-[#1a2d4a]" />
              </div>
              <div className="relative flex justify-center">
                <span className="bg-[#0f1f3a] px-4 text-[#6b7c93] text-xs uppercase tracking-wide">
                  or
                </span>
              </div>
            </div>

            {/* Request Access */}
            <div className="text-center">
              <Link
                to="/register"
                className="text-[#6b7c93] hover:text-[#2dd4bf] text-xs uppercase tracking-wide transition-colors"
              >
                Request Access
              </Link>
            </div>

            {/* Demo Info */}
            <p className="text-center text-[#4a5a72] text-xs uppercase tracking-wide">
              Demo: use emails like{" "}
              <code className="text-[#2dd4bf] font-semibold">admin@</code>,{" "}
              <code className="text-[#2dd4bf] font-semibold">trader@</code>, or{" "}
              <code className="text-[#2dd4bf] font-semibold">senior@</code>
            </p>
          </form>
        </div>

        {/* Footer */}
        <footer className="text-center text-[#4a5a72] text-xs uppercase tracking-wide space-y-2">
          <div className="flex items-center justify-center gap-4">
            <a href="#" className="hover:text-[#6b7c93] transition-colors">
              Terms
            </a>
            <span>•</span>
            <a href="#" className="hover:text-[#6b7c93] transition-colors">
              Privacy
            </a>
            <span>•</span>
            <a href="#" className="hover:text-[#6b7c93] transition-colors">
              Contact
            </a>
          </div>
          <p>© 2024 NQHUB. All rights reserved.</p>
        </footer>
      </div>
    </div>
  );
}
