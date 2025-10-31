import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { useI18n } from "@/state/app";
import { apiClient } from "@/services/api";

const ResetPassword: React.FC = () => {
  const { t } = useI18n();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) {
      setError(t("passwordRecovery.invalidToken"));
    }
  }, [token, t]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (newPassword.length < 8) {
      setError(t("passwordRecovery.passwordTooShort"));
      return;
    }

    if (newPassword !== confirmPassword) {
      setError(t("passwordRecovery.passwordMismatch"));
      return;
    }

    if (!token) {
      setError(t("passwordRecovery.invalidToken"));
      return;
    }

    setLoading(true);

    try {
      await apiClient.resetPassword(token, newPassword);
      setSuccess(true);
      setTimeout(() => {
        navigate("/");
      }, 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0A192F] via-[#0F2744] to-[#0A192F] flex items-center justify-center p-4">
        <div className="bg-gradient-to-br from-[#1A2332]/90 to-[#0F1D2E]/90 backdrop-blur-sm p-10 rounded-2xl border border-[#00D9FF]/20 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-white mb-3">
            {t("passwordRecovery.resetSuccess")}
          </h2>
          <p className="text-gray-400 mb-8">
            Redirecting to login...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0A192F] via-[#0F2744] to-[#0A192F] flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-10">
          <h1 className="text-5xl font-bold mb-2">
            <span className="text-[#FFB800]">NQ</span>
            <span className="text-white">HUB</span>
          </h1>
          <p className="text-gray-400 uppercase tracking-wider text-sm">
            Professional Trading Platform
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-gradient-to-br from-[#1A2332]/90 to-[#0F1D2E]/90 backdrop-blur-sm p-10 rounded-2xl border border-[#00D9FF]/20">
          <h2 className="text-3xl font-bold text-white mb-2">
            {t("passwordRecovery.resetPasswordTitle")}
          </h2>
          <p className="text-gray-400 mb-8">
            Choose a new password for your account
          </p>

          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t("passwordRecovery.newPassword")}
              </label>
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full px-4 py-3 bg-[#0A192F]/50 border border-gray-700 rounded-lg focus:ring-2 focus:ring-[#00D9FF] focus:border-transparent outline-none text-white placeholder-gray-500 transition-all"
                placeholder="••••••••"
                disabled={!token}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t("passwordRecovery.confirmPassword")}
              </label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-3 bg-[#0A192F]/50 border border-gray-700 rounded-lg focus:ring-2 focus:ring-[#00D9FF] focus:border-transparent outline-none text-white placeholder-gray-500 transition-all"
                placeholder="••••••••"
                disabled={!token}
              />
            </div>

            <button
              type="submit"
              disabled={loading || !token}
              className="w-full py-3 bg-gradient-to-r from-[#00D9FF] to-[#00B8D4] hover:from-[#00B8D4] hover:to-[#00D9FF] text-[#0A192F] font-bold rounded-lg transition-all duration-300 transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {loading ? "Resetting..." : t("passwordRecovery.resetButton")}
            </button>
          </form>

          <div className="mt-8 text-center">
            <Link
              to="/"
              className="text-[#00D9FF] hover:text-[#00B8D4] font-medium transition-colors"
            >
              {t("passwordRecovery.backToLogin")}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;
