//frontend/src/pages/AIAnalyzer.tsx
import { useState } from "react";
import { PageLayout } from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
// import { Globe } from "lucide-react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  Bot,
  Send,
  Loader2,
  Globe,
  Languages,
  FileText,
  Link,
  Image,
  Video,
  AlertTriangle,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useInView } from "react-intersection-observer";

interface Report {
  status: string;
  url: string;
  lang: string;
  title: string;
  text: string;
  images: string[];
  videos: string[];
  trigger_report: Record<string, any>;
  source_crebility: Array<{
    title: string;
    url: string;
    credibility: number;
  }>;
}

export default function AIAnalyzer() {
  const [urlInput, setUrlInput] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [report, setReport] = useState<Report | null>(null);

  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const handleAnalyze = async () => {
    if (!urlInput) return;

    setIsAnalyzing(true);
    setReport(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: urlInput }),
      });

      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

      const data = await response.json();
      setReport(data.report);
    } catch (error) {
      console.error("Error calling API:", error);
      setReport(null);
    } finally {
      setIsAnalyzing(false);
    }
  };

return (
  <PageLayout className="py-8">
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6 }}
      className="space-y-10"
    >
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-100 to-blue-200 rounded-full shadow-sm"
        >
          <Bot className="h-5 w-5 text-blue-600" />
          <span className="text-blue-700 font-medium">AI Fact Analyzer</span>
        </motion.div>
        <h1 className="text-4xl md:text-6xl font-bold text-gradient">
          Fact Check Any URL
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Paste a link to analyze its credibility, sources, and content.
        </p>
      </div>

      {/* Two Column Layout */}
<div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-6xl mx-auto w-full">
  {/* LEFT COLUMN */}
  <div className="space-y-6">
    {/* Input Section */}
    <Card className="glass-card shadow-lg border border-blue-100">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-blue-600">
          <Link className="h-5 w-5" />
          Submit URL
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col sm:flex-row gap-3">
          <Input
            type="url"
            placeholder="🔗 Enter a news/article link..."
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            className="flex-grow px-4 py-3 rounded-lg border focus:ring-2 focus:ring-blue-500"
          />
          <Button
            onClick={handleAnalyze}
            disabled={isAnalyzing || !urlInput}
            className="gradient-primary px-6 py-3 rounded-lg shadow-md"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Analyze
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>

    {/* Source Credibility */}
    {report && report.source_crebility && (
  <Card className="border-l-4 border-green-400 shadow-sm">
    <CardHeader>
      <CardTitle className="text-green-600 flex items-center gap-2">
        ✅ Source Credibility
      </CardTitle>
    </CardHeader>
    <CardContent className="space-y-3">
      {/* Domain */}
      <p>
        <strong>Domain:</strong> {report.source_crebility.domain}
      </p>

      {/* Credibility Label & Score */}
      <p>
        <strong>Credibility:</strong>{" "}
        <span className="px-2 py-1 rounded bg-gray-100">
          {report.source_crebility.label} (
          {(report.source_crebility.score * 100).toFixed(1)}%)
        </span>
      </p>

      {/* Reasons */}
      {/* {report.source_crebility.reasons?.length > 0 && (
        <div>
          <strong>Reasons:</strong>
          <ul className="list-disc list-inside mt-1 text-sm text-gray-700">
            {report.source_crebility.reasons.map((reason, idx) => (
              <li key={idx}>{reason}</li>
            ))}
          </ul>
        </div>
      )} */}

      {/* Signals */}
      {report.source_crebility.signals && (
        <div className="text-sm mt-2">
          <strong>Signals:</strong>
          <ul className="list-disc list-inside text-gray-700 mt-1">
            <li>
              <strong>NewsAPI:</strong>{" "}
              {report.source_crebility.signals.newsapi.present
                ? "✅ Present"
                : "❌ Not Present"}
            </li>
            <li>
              <strong>GNews:</strong>{" "}
              {report.source_crebility.signals.gnews.present
                ? "✅ Present"
                : "❌ Not Present"}
            </li>
            <li>
              <strong>Fact Check:</strong>{" "}
              {report.source_crebility.signals.factcheck.found
                ? "✅ Found"
                : "❌ Not Found"}
            </li>
            <li>
              <strong>Domain Age:</strong>{" "}
              {report.source_crebility.signals.domain_age_days
                ? `${report.source_crebility.signals.domain_age_days} days`
                : "Unknown"}
            </li>
          </ul>
        </div>
      )}
    </CardContent>
  </Card>
)}
    {/* Risk Assessment */}
    {report && (
      <Card className="border-l-4 border-red-400 shadow-sm">
        <CardHeader>
          <CardTitle className="text-red-600 flex items-center gap-2">
            ⚠️ Risk Assessment
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <div
              className={`w-3 h-3 rounded-full ${
                report.trigger_report.risk_score < 0.3
                  ? "bg-green-500"
                  : report.trigger_report.risk_score < 0.6
                  ? "bg-yellow-500"
                  : "bg-red-500"
              }`}
            ></div>
            <span className="font-medium">
              {(report.trigger_report.risk_score * 100)}%
            </span>
          </div>
        </CardContent>
      </Card>
    )}
  </div>

  {/* RIGHT COLUMN */}
  <div className="space-y-6">
    {/* Article Info */}
    {report && (
      <Card className="border-l-4 border-blue-400 shadow-sm">
        <CardHeader>
          <CardTitle className="text-blue-600 flex items-center gap-2">
            <Link className="h-5 w-5" />
            Article Info
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground break-all">
            <strong>URL:</strong> {report.url}
          </p>
          <p className="text-sm mt-1 flex items-center gap-2">
  <Globe className="w-4 h-4 text-blue-500" />
  <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">
    {report.lang.toUpperCase()}
  </span>
</p>
        </CardContent>
      </Card>
    )}

    {/* Flagged Phrases */}
    {report && (
      <Card className="border-l-4 border-yellow-400 shadow-sm">
        <CardHeader>
          <CardTitle className="text-yellow-600 flex items-center gap-2">
            🚩 Flagged Phrases
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {report.trigger_report.matched_triggers.slice(0, 5).map((t, i) => (
            <div key={i} className="p-3 border rounded-lg bg-yellow-50">
              <p className="font-medium">"{t.phrase}"</p>
              <p className="text-xs text-muted-foreground">{t.category}</p>
              {t.snippets && (
                <p className="text-sm italic text-muted-foreground mt-1">
                  ...{t.snippets[0]}...
                </p>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    )}
  </div>
</div>
    </motion.div>
  </PageLayout>
);
}
