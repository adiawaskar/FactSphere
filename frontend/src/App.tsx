//frontend/src/App.tsx
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { NotificationsProvider } from "@/contexts/NotificationsContext";
import Index from "./pages/Index";
import DeepfakeDetection from "./pages/DeepfakeDetection";
import GlobalTrends from "./pages/GlobalTrends";
import AIAnalyzer from "./pages/AIAnalyzer";
import AskAI from "./pages/AskAI";
import KnowledgeBase from "./pages/KnowledgeBase";
import About from "./pages/About";
import Notifications from "./pages/Notifications";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <NotificationsProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/deepfake-detection" element={<DeepfakeDetection />} />
            <Route path="/social-trends" element={<GlobalTrends />} />
            <Route path="/ai-analyzer" element={<AIAnalyzer />} />
            <Route path="/ask-ai" element={<AskAI />} />
            <Route path="/knowledge-base" element={<KnowledgeBase />} />
            <Route path="/about" element={<About />} />
            <Route path="/notifications" element={<Notifications />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </NotificationsProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
