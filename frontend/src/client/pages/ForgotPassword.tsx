import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useI18n } from "@/state/app";
import { apiClient } from "@/services/api";

const ForgotPassword: React.FC = () => {
  const { t } = useI18n();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await apiClient.forgotPassword(email);
      setSubmitted(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0A192F] via-[#0F2744] to-[#0A192F] flex items-center justify-center p-4">
        <div className="bg-gradient-to-br from-[#1A2332]/90 to-[#0F1D2E]/90 backdrop-blur-sm p-10 rounded-2xl border border-[#00D9FF]/20 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-[#00D9FF]/10 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-[#00D9FF]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-white mb-3">
            {t("passwordRecovery.checkEmail")}
          </h2>
          <p className="text-gray-400 mb-8">
            If the email exists in our system, you will receive a password reset link shortly.
          </p>
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-6 py-3 bg-[#00D9FF]/10 hover:bg-[#00D9FF]/20 text-[#00D9FF] font-medium rounded-lg transition-colors border border-[#00D9FF]/20"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            {t("passwordRecovery.backToLogin")}
          </Link>
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
            {t("passwordRecovery.forgotPasswordTitle")}
          </h2>
          <p className="text-gray-400 mb-8">
            {t("passwordRecovery.enterEmailInstruction")}
          </p>

          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t("auth.email")}
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-[#0A192F]/50 border border-gray-700 rounded-lg focus:ring-2 focus:ring-[#00D9FF] focus:border-transparent outline-none text-white placeholder-gray-500 transition-all"
                placeholder="your@email.com"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-[#00D9FF] to-[#00B8D4] hover:from-[#00B8D4] hover:to-[#00D9FF] text-[#0A192F] font-bold rounded-lg transition-all duration-300 transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {loading ? "Sending..." : t("passwordRecovery.sendResetLink")}
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

export default ForgotPassword;
