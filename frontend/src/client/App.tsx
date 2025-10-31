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
import NotFound from "./pages/NotFound";
import Dashboard from "./pages/Dashboard";
import DataModule from "./pages/DataModule";
import WithLayout from "./pages/Placeholders";
import { AppProvider, useAuth, Role } from "@/state/app";

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
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/register" element={<Register />} />
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
              path="/data/analysis"
              element={
                <ProtectedRoute>
                  <DataModule defaultTab="analysis" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/backtesting"
              element={
                <ProtectedRoute>
                  <WithLayout title="Backtesting Module" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/bot"
              element={
                <ProtectedRoute>
                  <WithLayout
                    title="BOT Module"
                    description="Trader access required"
                  />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <WithLayout title="Settings" />
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
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </AppProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

createRoot(document.getElementById("root")!).render(<App />);
