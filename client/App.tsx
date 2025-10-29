import "./global.css";

import { Toaster } from "@/components/ui/toaster";
import { createRoot } from "react-dom/client";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import Dashboard from "./pages/Dashboard";
import DataModule from "./pages/DataModule";
import WithLayout from "./pages/Placeholders";
import { AppProvider, useAuth } from "@/state/app";

const queryClient = new QueryClient();

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/" replace />;
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
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/data" element={<ProtectedRoute><DataModule /></ProtectedRoute>} />
            <Route path="/data/charts" element={<ProtectedRoute><DataModule defaultTab="charts" /></ProtectedRoute>} />
            <Route path="/data/analysis" element={<ProtectedRoute><DataModule defaultTab="analysis" /></ProtectedRoute>} />
            <Route path="/backtesting" element={<ProtectedRoute><WithLayout title="Backtesting Module" /></ProtectedRoute>} />
            <Route path="/bot" element={<ProtectedRoute><WithLayout title="BOT Module" description="Trader access required" /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><WithLayout title="Settings" /></ProtectedRoute>} />
            <Route path="/help" element={<ProtectedRoute><WithLayout title="Help & Docs" /></ProtectedRoute>} />
            <Route path="/admin/users" element={<ProtectedRoute><WithLayout title="User Management" /></ProtectedRoute>} />
            <Route path="/stats" element={<ProtectedRoute><WithLayout title="Stats" /></ProtectedRoute>} />
            <Route path="/tradecademy" element={<ProtectedRoute><WithLayout title="Tradecademy" /></ProtectedRoute>} />
            <Route path="/auth/request-access" element={<WithLayout title="Request Access" />} />
            <Route path="/auth/forgot-password" element={<WithLayout title="Password Recovery" />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </AppProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

createRoot(document.getElementById("root")!).render(<App />);
