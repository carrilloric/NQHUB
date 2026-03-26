import "./global.css";

import { Toaster } from "@/components/ui/toaster";
import { createRoot } from "react-dom/client";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Index from "./pages/Index";
import Register from "./pages/Register";
import Invitations from "./pages/Invitations";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import NotFound from "./pages/NotFound";
import Dashboard from "./pages/Dashboard";
import DataModule from "./pages/DataModule";
import StatisticalAnalysis from "./pages/StatisticalAnalysis";
import WithLayout from "./pages/Placeholders";
import ChartTest from "./pages/ChartTest";
// New page imports
import Features from "./pages/Features";
import BacktestingRuleBased from "./pages/BacktestingRuleBased";
import BacktestingAI from "./pages/BacktestingAI";
import MachineLearning from "./pages/MachineLearning";
import Approval from "./pages/Approval";
import Bot from "./pages/Bot";
import Orders from "./pages/Orders";
import RiskManagement from "./pages/RiskManagement";
import Trades from "./pages/Trades";
import Settings from "./pages/Settings";
import Strategies from "./pages/Strategies";
import Assistant from "./pages/Assistant";
import { AppProvider, useAuth, Role } from "@/state/app";
import { ServerTimeProvider } from "@/state/server-time";

const queryClient = new QueryClient();

const ProtectedRoute: React.FC<{
  children: React.ReactNode;
  requiredRole?: Role;
}> = ({ children, requiredRole }) => {
  const { isAuthenticated, user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  if (requiredRole && user?.role !== requiredRole) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AppProvider>
        <ServerTimeProvider>
          <BrowserRouter>
            <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/data"
              element={
                <ProtectedRoute>
                  <DataModule />
                </ProtectedRoute>
              }
            />
            <Route
              path="/data/charts"
              element={
                <ProtectedRoute>
                  <DataModule defaultTab="charts" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/statistical-analysis"
              element={
                <ProtectedRoute>
                  <StatisticalAnalysis />
                </ProtectedRoute>
              }
            />
            <Route
              path="/features"
              element={
                <ProtectedRoute>
                  <Features />
                </ProtectedRoute>
              }
            />
            <Route
              path="/backtesting/rule-based"
              element={
                <ProtectedRoute>
                  <BacktestingRuleBased />
                </ProtectedRoute>
              }
            />
            <Route
              path="/backtesting/ai"
              element={
                <ProtectedRoute>
                  <BacktestingAI />
                </ProtectedRoute>
              }
            />
            <Route
              path="/ml"
              element={
                <ProtectedRoute>
                  <MachineLearning />
                </ProtectedRoute>
              }
            />
            <Route
              path="/approval"
              element={
                <ProtectedRoute>
                  <Approval />
                </ProtectedRoute>
              }
            />
            <Route
              path="/bot"
              element={
                <ProtectedRoute>
                  <Bot />
                </ProtectedRoute>
              }
            />
            <Route
              path="/orders"
              element={
                <ProtectedRoute>
                  <Orders />
                </ProtectedRoute>
              }
            />
            <Route
              path="/risk"
              element={
                <ProtectedRoute>
                  <RiskManagement />
                </ProtectedRoute>
              }
            />
            <Route
              path="/trades"
              element={
                <ProtectedRoute>
                  <Trades />
                </ProtectedRoute>
              }
            />
            <Route
              path="/strategies"
              element={
                <ProtectedRoute>
                  <Strategies />
                </ProtectedRoute>
              }
            />
            <Route
              path="/assistant"
              element={
                <ProtectedRoute>
                  <Assistant />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <Settings />
                </ProtectedRoute>
              }
            />
            <Route
              path="/help"
              element={
                <ProtectedRoute>
                  <WithLayout title="Help & Docs" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/users"
              element={
                <ProtectedRoute requiredRole="admin">
                  <WithLayout title="User Management" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/invitations"
              element={
                <ProtectedRoute requiredRole="admin">
                  <Invitations />
                </ProtectedRoute>
              }
            />
            <Route
              path="/stats"
              element={
                <ProtectedRoute>
                  <WithLayout title="Stats" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/tradecademy"
              element={
                <ProtectedRoute>
                  <WithLayout title="Tradecademy" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/auth/request-access"
              element={<WithLayout title="Request Access" />}
            />
            <Route
              path="/auth/forgot-password"
              element={<WithLayout title="Password Recovery" />}
            />
            <Route path="/chart-test" element={<ChartTest />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </ServerTimeProvider>
    </AppProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

// Initialize MSW for development
async function enableMocking() {
  if (process.env.NODE_ENV !== 'development') {
    return;
  }

  const { worker } = await import('../mocks/browser');

  // Start the worker with onUnhandledRequest set to 'bypass' to allow real API calls
  return worker.start({
    onUnhandledRequest: 'bypass',
  });
}

// Start the app with MSW enabled in development
enableMocking().then(() => {
  createRoot(document.getElementById("root")!).render(<App />);
});
