// //frontend/src/pages/AIAnalyzer.tsx
// import { useState } from "react";
// import { PageLayout } from "@/components/layout/PageLayout";
// import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
// import { Button } from "@/components/ui/button";
// import { Input } from "@/components/ui/input";
// // import { Globe } from "lucide-react";

// import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
// import { Badge } from "@/components/ui/badge";
// import {
//   Bot,
//   Send,
//   Loader2,
//   Globe,
//   Languages,
//   FileText,
//   Link,
//   Image,
//   Video,
//   AlertTriangle,
// } from "lucide-react";
// import { motion, AnimatePresence } from "framer-motion";
// import { useInView } from "react-intersection-observer";

// interface Report {
//   status: string;
//   url: string;
//   lang: string;
//   title: string;
//   text: string;
//   images: string[];
//   videos: string[];
//   trigger_report: Record<string, any>;
//   source_credibility: Array<{
//     title: string;
//     url: string;
//     credibility: number;
//   }>;
// }

// export default function AIAnalyzer() {
//   const [input, setInput] = useState("");
//   const [inputType,setInputType]=useState("");
//   const [isAnalyzing, setIsAnalyzing] = useState(false);
//   const [report, setReport] = useState<Report | null>(null);

//   const [ref, inView] = useInView({
//     triggerOnce: true,
//     threshold: 0.1,
//   });

//   const handleAnalyze = async () => {
//     if (!input) return;

//     setIsAnalyzing(true);
//     setReport(null);

//     try {
//       const response = await fetch("http://127.0.0.1:8000/api/analyze", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ type:inputType, input: input }),
//       });

//       if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

//       const data = await response.json();
//       setReport(data.report);
//     } catch (error) {
//       console.error("Error calling API:", error);
//       setReport(null);
//     } finally {
//       setIsAnalyzing(false);
//     }
//   };

// return (
//   <PageLayout className="py-8">
//     <motion.div
//       ref={ref}
//       initial={{ opacity: 0, y: 50 }}
//       animate={inView ? { opacity: 1, y: 0 } : {}}
//       transition={{ duration: 0.6 }}
//       className="space-y-10"
//     >
//       {/* Hero Section */}
//       <div className="text-center space-y-4">
//         <motion.div
//           initial={{ scale: 0 }}
//           animate={{ scale: 1 }}
//           transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
//           className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-100 to-blue-200 rounded-full shadow-sm"
//         >
//           <Bot className="h-5 w-5 text-blue-600" />
//           <span className="text-blue-700 font-medium">AI Fact Analyzer</span>
//         </motion.div>
//         <h1 className="text-4xl md:text-6xl font-bold text-gradient">
//           Fact Check Any URL
//         </h1>
//         <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
//           Paste a link to analyze its credibility, sources, and content.
//         </p>
//       </div>

//       {/* Two Column Layout */}
// <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-6xl mx-auto w-full">
//   {/* LEFT COLUMN */}
//   <div className="space-y-6">
//     {/* Input Section */}
// <Card className="glass-card shadow-lg border border-blue-100">
//   <CardHeader>
//     <CardTitle className="flex items-center gap-2 text-blue-600">
//       <Link className="h-5 w-5" />
//       Submit Content
//     </CardTitle>
//   </CardHeader>
//   <CardContent>
//     <Tabs defaultValue="url" className="w-full">
//       <TabsList className="grid grid-cols-3 mb-4">
//         <TabsTrigger value="url">URL</TabsTrigger>
//         <TabsTrigger value="text">Text</TabsTrigger>
//         <TabsTrigger value="file">File</TabsTrigger>
//       </TabsList>

//       {/* URL Input */}
//       <TabsContent value="url">
//         <div className="flex flex-col sm:flex-row gap-3">
//           <Input
//             type="url"
//             placeholder="🔗 Enter a news/article link..."
//             value={input}
//             onChange={(e) => {setInput(e.target.value);
//                setInputType("url")}}
//             className="flex-grow px-4 py-3 rounded-lg border focus:ring-2 focus:ring-blue-500"
//           />
//           <Button
//             onClick={handleAnalyze}
//             disabled={isAnalyzing || !input}
//             className="gradient-primary px-6 py-3 rounded-lg shadow-md"
//           >
//             {isAnalyzing ? (
//               <>
//                 <Loader2 className="mr-2 h-4 w-4 animate-spin" />
//                 Analyzing...
//               </>
//             ) : (
//               <>
//                 <Send className="mr-2 h-4 w-4" />
//                 Analyze
//               </>
//             )}
//           </Button>
//         </div>
//       </TabsContent>

//       {/* Text Input */}
//       <TabsContent value="text">
//         <div className="space-y-3">
//           <textarea
//             placeholder="📝 Paste article text here..."
//             value={input}
//             onChange={(e) => {setInput(e.target.value);
//                setInputType("text")}}
//             className="w-full px-4 py-3 rounded-lg border focus:ring-2 focus:ring-blue-500 min-h-[120px]"
//           />
//           <Button
//             onClick={handleAnalyze}
//             disabled={isAnalyzing}
//             className="gradient-primary px-6 py-3 rounded-lg shadow-md"
//           >
//             {isAnalyzing ? (
//               <>
//                 <Loader2 className="mr-2 h-4 w-4 animate-spin" />
//                 Analyzing...
//               </>
//             ) : (
//               <>
//                 <Send className="mr-2 h-4 w-4" />
//                 Analyze
//               </>
//             )}
//           </Button>
//         </div>
//       </TabsContent>

//       {/* File Upload */}
//       <TabsContent value="file">
//         <div className="space-y-3">
//           <Input
//             type="file"
//             accept=".txt,.pdf,.docx"
//             className="cursor-pointer"
//           />
//           <Button
//             onClick={handleAnalyze}
//             disabled={isAnalyzing}
//             className="gradient-primary px-6 py-3 rounded-lg shadow-md"
//           >
//             {isAnalyzing ? (
//               <>
//                 <Loader2 className="mr-2 h-4 w-4 animate-spin" />
//                 Analyzing...
//               </>
//             ) : (
//               <>
//                 <Send className="mr-2 h-4 w-4" />
//                 Analyze
//               </>
//             )}
//           </Button>
//         </div>
//       </TabsContent>
//     </Tabs>
//   </CardContent>
// </Card>

//     {/* Source Credibility */}
//     {report && report.source_credibility && (
//   <Card className="border-l-4 border-green-400 shadow-sm">
//     <CardHeader>
//       <CardTitle className="text-green-600 flex items-center gap-2">
//         ✅ Source Credibility
//       </CardTitle>
//     </CardHeader>
//     <CardContent className="space-y-3">
//       {/* Domain */}
//       <p>
//         <strong>Domain:</strong> {report.source_credibility.domain}
//       </p>

//       {/* Credibility Label & Score */}
//       <p>
//         <strong>Credibility:</strong>{" "}
//         <span className="px-2 py-1 rounded bg-gray-100">
//           {report.source_credibility.label} (
//           {(report.source_credibility.score * 100).toFixed(1)}%)
//         </span>
//       </p>

   
      
//       {/* Signals */}
//       {report.source_credibility.signals && (
//         <div className="text-sm mt-2">
//           <strong>Signals:</strong>
//           <ul className="list-disc list-inside text-gray-700 mt-1">
//             {/* <li>
//               <strong>NewsAPI:</strong>{" "}
//               {report.source_credibility.signals.newsapi.present
//                 ? "✅ Present"
//                 : "❌ Not Present"}
//             </li> */}
//             <li>
//               <strong>GNews:</strong>{" "}
//               {report.source_credibility.signals.gnews.present
//                 ? "✅ Present"
//                 : "❌ Not Present"}
//             </li>
//             <li>
//               <strong>Fact Check:</strong>{" "}
//               {report.source_credibility.signals.factcheck.found
//                 ? "✅ Found"
//                 : "❌ Not Found"}
//             </li>
//             <li>
//               <strong>Domain Age:</strong>{" "}
//               {report.source_credibility.signals.domain_age_days
//                 ? `${report.source_credibility.signals.domain_age_days} days`
//                 : "Unknown"}
//             </li>
//           </ul>
//         </div>
//       )}
//     </CardContent>
//   </Card>
// )}

// {/* Reverse Image Search Results */}
// {report && report.reverse_img && report.reverse_img.status === "success" && (
//   <Card className="border-l-4 border-red-400 shadow-sm">
//     <CardHeader>
//       <CardTitle className="text-red-600 flex items-center gap-2">
//         <Image className="h-5 w-5" />
//         Reverse Image Search Results
//       </CardTitle>
//     </CardHeader>
//     <CardContent className="space-y-5">
//       <p className="text-sm text-muted-foreground">
//         <strong>Article Title:</strong> {report.reverse_img.article_title}
//       </p>

//       {report.reverse_img.image_results.map((img, idx) => (
//         <div
//           key={idx}
//           className="p-4 rounded-lg border bg-purple-50 space-y-3 shadow-sm"
//         >
//           <div className="flex flex-col sm:flex-row sm:items-center gap-3">
//             <img
//               src={img.image_url}
//               alt={`Image ${idx + 1}`}
//               className="w-full sm:w-40 h-auto rounded-lg border"
//             />
//             <div>
//               <p className="font-medium text-red-700">
//                 Image {idx + 1} — Top Matches:
//               </p>
//             </div>
//           </div>

//           {/* Best Matches */}
//           <div className="mt-3 space-y-2">
//             {img.best_matches.map((match, j) => (
//               <div
//                 key={j}
//                 className="p-3 border rounded-lg bg-white hover:bg-purple-100 transition"
//               >
//                 <p className="font-medium text-gray-800">
//                   {match.title || "Untitled"}
//                 </p>
//                 <p className="text-sm text-gray-600">
//                   <strong>Source:</strong> {match.source}
//                 </p>
//                 <p className="text-sm text-gray-600">
//                   <strong>Category:</strong> {match.category}
//                 </p>
//                 <p className="text-sm text-gray-600">
//                   <strong>Score:</strong> {(match.score * 100).toFixed(0)}%
//                 </p>
//                 <a
//                   href={match.link}
//                   target="_blank"
//                   rel="noopener noreferrer"
//                   className="text-sm text-blue-600 hover:underline break-all"
//                 >
//                   {match.link}
//                 </a>
//               </div>
//             ))}
//           </div>
//         </div>
//       ))}
//     </CardContent>
//   </Card>
// )}
//     {/* Risk Assessment */}
//     {report && (
//       <Card className="border-l-4 border-red-400 shadow-sm">
//         <CardHeader>
//           <CardTitle className="text-red-600 flex items-center gap-2">
//             ⚠️ Risk Assessment
//           </CardTitle>
//         </CardHeader>
//         <CardContent>
//           <div className="flex items-center gap-2">
//             <div
//               className={`w-3 h-3 rounded-full ${
//                 report.trigger_report.risk_score < 0.3
//                   ? "bg-green-500"
//                   : report.trigger_report.risk_score < 0.6
//                   ? "bg-yellow-500"
//                   : "bg-red-500"
//               }`}
//             ></div>
//             <span className="font-medium">
//               {(report.trigger_report.risk_score * 100)}%
//             </span>
//           </div>
//         </CardContent>
//       </Card>
//     )}
//   </div>

//   {/* RIGHT COLUMN */}
//   <div className="space-y-6">
//     {/* Article Info */}
//     {report && (
//       <Card className="border-l-4 border-blue-400 shadow-sm">
//         <CardHeader>
//           <CardTitle className="text-blue-600 flex items-center gap-2">
//             <Link className="h-5 w-5" />
//             Article Info
//           </CardTitle>
//         </CardHeader>
//         <CardContent>
//           <p className="text-sm text-muted-foreground break-all">
//             <strong>URL:</strong> {report.url}
//           </p>
//            <p className="text-sm text-muted-foreground break-all">
//             <strong>Title:</strong> {report.title}
//           </p>
//           <p className="text-sm mt-1 flex items-center gap-2">
//   <Globe className="w-4 h-4 text-blue-500" />
//   <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">
//     {report.lang.toUpperCase()}
//   </span>
// </p>
//         </CardContent>
//       </Card>
//     )}

//     {/* Flagged Phrases */}
//     {report && (
//       <Card className="border-l-4 border-yellow-400 shadow-sm">
//         <CardHeader>
//           <CardTitle className="text-yellow-600 flex items-center gap-2">
//             🚩 Flagged Phrases
//           </CardTitle>
//         </CardHeader>
//         <CardContent className="space-y-3">
//           {report.trigger_report.list_of_phrases.map((t, i) => (
//             <div key={i} className="p-3 border rounded-lg bg-yellow-50">
//               <p className="font-medium">"{t.phrase}"</p>
//               {/* <p className="text-xs text-muted-foreground">{t.category}</p> */}
//               {/* {t.snippets && (
//                 <p className="text-sm italic text-muted-foreground mt-1">
//                   ...{t.snippets[0]}...
//                 </p>
//               )} */}
//                {/* Show first 2 snippets (or all if you want) */}
//     {/* {t.snippets?.slice(0, 2).map((snippet, idx) => ( */}
//       <p  className="text-sm italic text-muted-foreground mt-1">
//         ...{t.snippet}...
//       </p>
    
//             </div>
//           ))}
//         </CardContent>
//       </Card>
//     )}

//     {/* Cross Verify Results */}
// {report && report.cross_verify && (
//   <Card className="border-l-4 border-purple-500 shadow-lg">
//     <CardHeader>
//       <CardTitle className="text-purple-600 flex items-center gap-2">
//         <Globe className="h-5 w-5" />
//         Cross Verification Results
//       </CardTitle>
//     </CardHeader>
//     <CardContent className="space-y-4">
//       {/* Summary */}
//       <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm text-gray-700">
//         <p><strong>Article:</strong> {report.cross_verify.article.title}</p>
//         <p><strong>Source:</strong> {report.cross_verify.article.source}</p>
//         <p>
//           <strong>Verdict:</strong>{" "}
//           <span
//             className={`font-medium ${
//               report.cross_verify.verification.verdict === "HIGHLY_CREDIBLE"
//                 ? "text-green-600"
//                 : report.cross_verify.verification.verdict === "UNVERIFIED"
//                 ? "text-yellow-600"
//                 : "text-red-600"
//             }`}
//           >
//             {report.cross_verify.verification.verdict}
//           </span>
//         </p>
//         <p>
//           <strong>Confidence:</strong>{" "}
//           {(report.cross_verify.verification.confidence * 100).toFixed(0)}%
//         </p>
//         <p>
//           <strong>Credibility Score:</strong>{" "}
//           {(report.cross_verify.verification.credibility_score * 100).toFixed(0)}%
//         </p>
//         <p>
//           <strong>Consensus:</strong> {report.cross_verify.consensus_analysis.analysis}
//         </p>
//         <p>
//           <strong>Sources Analyzed:</strong> {report.cross_verify.consensus_analysis.total_sources}
//         </p>
//         <p>
//           <strong>Confirmations:</strong> {report.cross_verify.consensus_analysis.confirmations?.length || 0}
//         </p>
//         <p>
//           <strong>Contradictions:</strong> {report.cross_verify.consensus_analysis.contradictions?.length || 0}
//         </p>
//       </div>

//       <div className="border-t border-gray-300 my-2"></div>

//       {/* Top Confirmations */}
//       <div>
//         <h3 className="text-sm font-semibold text-gray-800 mb-2">✅ Top Confirmations:</h3>
//         <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
//           {report.cross_verify.consensus_analysis.confirmations?.slice(0, 3).map((conf, idx) => (
//             <li key={idx}>
//               <b>{conf.source}:</b> {conf.title.slice(0, 85)}...
//             </li>
//           )) || <li>No confirmations available</li>}
//         </ul>
//       </div>

//       <div className="border-t border-gray-300 my-2"></div>

//       {/* Related Articles */}
//       <div>
//         <h3 className="text-sm font-semibold text-gray-800 mb-2">📰 Related Articles:</h3>
//         <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
//           {report.cross_verify.similar_articles?.slice(0, 5).map((art, idx) => (
//             <li key={idx}>
//               <a
//                 href={art.url}
//                 target="_blank"
//                 rel="noopener noreferrer"
//                 className="text-blue-600 hover:underline"
//               >
//                 {art.title.slice(0, 80)}...
//               </a>{" "}
//               <span className="text-gray-500">({art.source})</span>
//             </li>
//           )) || <li>No similar articles found</li>}
//         </ul>
//       </div>
//     </CardContent>
//   </Card>
// )}
//   </div>
// </div>
//     </motion.div>
//   </PageLayout>
// );
// }
// frontend/src/pages/AIAnalyzer.tsx
import { useState } from "react";
import { PageLayout } from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
  Search,
  Shield,
  CheckCircle,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useInView } from "react-intersection-observer";
import Lottie from "lottie-react";
import analysisAnimation from "@/assets/lottie/analysis.json"; // Add this Lottie file

interface Report {
  status: string;
  url: string;
  lang: string;
  title: string;
  text: string;
  images: string[];
  videos: string[];
  trigger_report: {
    risk_score: number;
    list_of_phrases: Array<{
      phrase: string;
      snippet: string;
    }>;
  };
  source_credibility: {
    domain: string;
    label: string;
    score: number;
    signals: {
      gnews: { present: boolean };
      factcheck: { found: boolean };
      domain_age_days: number;
    };
  };
  reverse_img?: {
    status: string;
    article_title: string;
    image_results: Array<{
      image_url: string;
      best_matches: Array<{
        title: string;
        source: string;
        category: string;
        score: number;
        link: string;
      }>;
    }>;
  };
  cross_verify?: {
    article: {
      title: string;
      source: string;
    };
    verification: {
      verdict: string;
      confidence: number;
      credibility_score: number;
    };
    consensus_analysis: {
      analysis: string;
      total_sources: number;
      confirmations: Array<{
        source: string;
        title: string;
      }>;
      contradictions: Array<any>;
    };
    similar_articles: Array<{
      title: string;
      url: string;
      source: string;
    }>;
  };
}

export default function AIAnalyzer() {
  const [input, setInput] = useState("");
  const [inputType, setInputType] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [report, setReport] = useState<Report | null>(null);

  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const handleAnalyze = async () => {
    if (!input) return;

    setIsAnalyzing(true);
    setReport(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: inputType, input: input }),
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

  // Get credibility badge color
  // Helper functions for final risk assessment
const getFinalRiskColor = (score: number) => {
  if (score < 0.3) return "bg-green-500";
  if (score < 0.6) return "bg-yellow-500";
  return "bg-red-500";
};

const getFinalRiskBorderColor = (score: number) => {
  if (score < 0.3) return "border-green-400";
  if (score < 0.6) return "border-yellow-400";
  return "border-red-400";
};

const getFinalRiskTextColor = (score: number) => {
  if (score < 0.3) return "text-green-600";
  if (score < 0.6) return "text-yellow-600";
  return "text-red-600";
};

const getFinalRiskBadgeColor = (score: number) => {
  if (score < 0.3) return "bg-green-100 text-green-800 border-green-200";
  if (score < 0.6) return "bg-yellow-100 text-yellow-800 border-yellow-200";
  return "bg-red-100 text-red-800 border-red-200";
};

const getFinalRiskIcon = (score: number) => {
  if (score < 0.3) return "✅";
  if (score < 0.6) return "⚠️";
  return "🚨";
};

const getFinalRiskLevel = (score: number) => {
  if (score < 0.3) return "Low Risk";
  if (score < 0.6) return "Medium Risk";
  return "High Risk";
};
  return (
    <PageLayout className="py-8 bg-gradient-to-br from-blue-50 via-white to-purple-50 min-h-screen w-full">
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-7xl mx-auto w-full">
          {/* LEFT COLUMN - Input & Results */}
          <div className="space-y-6">
            {/* Input Section */}
            <Card className="glass-card shadow-lg border border-blue-100">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-blue-600">
                  <Link className="h-5 w-5" />
                  Submit Content
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="url" className="w-full">
                  <TabsList className="grid grid-cols-3 mb-4">
                    <TabsTrigger value="url">URL</TabsTrigger>
                    <TabsTrigger value="text">Text</TabsTrigger>
                    <TabsTrigger value="file">File</TabsTrigger>
                  </TabsList>

                  {/* URL Input */}
                  <TabsContent value="url">
                    <div className="flex flex-col sm:flex-row gap-3">
                      <Input
                        type="url"
                        placeholder="🔗 Enter a news/article link..."
                        value={input}
                        onChange={(e) => {
                          setInput(e.target.value);
                          setInputType("url");
                        }}
                        className="flex-grow px-4 py-3 rounded-lg border focus:ring-2 focus:ring-blue-500"
                      />
                      <Button
                        onClick={handleAnalyze}
                        disabled={isAnalyzing || !input}
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
                  </TabsContent>

                  {/* Text Input */}
                  <TabsContent value="text">
                    <div className="space-y-3">
                      <textarea
                        placeholder="📝 Paste article text here..."
                        value={input}
                        onChange={(e) => {
                          setInput(e.target.value);
                          setInputType("text");
                        }}
                        className="w-full px-4 py-3 rounded-lg border focus:ring-2 focus:ring-blue-500 min-h-[120px]"
                      />
                      <Button
                        onClick={handleAnalyze}
                        disabled={isAnalyzing || !input}
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
                  </TabsContent>

                  {/* File Upload */}
                  <TabsContent value="file">
                    <div className="space-y-3">
                      <Input
                        type="file"
                        accept=".txt,.pdf,.docx"
                        className="cursor-pointer"
                      />
                      <Button
                        onClick={handleAnalyze}
                        disabled={isAnalyzing}
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
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>

            {/* Analysis Features */}
               {!report && <Card className="shadow-lg border border-blue-100">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-blue-600">
                      <CheckCircle className="h-5 w-5" />
                      What We Analyze
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {[
                      "Source Credibility Check",
                      "Fact Verification",
                      "Bias Detection", 
                      "Cross-Reference Analysis",
                      "Risk Assessment",
                      "Image Reverse Search",
                      "Flagged Content Detection",
                      "Multi-language Support"
                    ].map((feature, index) => (
                      <div key={index} className="flex items-center gap-3 text-sm">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <span className="text-gray-700">{feature}</span>
                      </div>
                    ))}
                  </CardContent>
                </Card>}


            {/* Results Section - Only show when report exists */}
            <AnimatePresence>
              {report && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-6"
                >
                  {/* Source Credibility */}
                  {report.source_credibility && (
                    <Card className="border-l-4 border-green-400 shadow-sm">
                      <CardHeader>
                        <CardTitle className="text-green-600 flex items-center gap-2">
                          ✅ Source Credibility
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <p>
                          <strong>Domain:</strong> {report.source_credibility.domain}
                        </p>
                        <p>
                          <strong>Credibility:</strong>{" "}
                          <span className="px-2 py-1 rounded bg-gray-100">
                            {report.source_credibility.label} (
                            {(report.source_credibility.score * 100).toFixed(1)}%)
                          </span>
                        </p>
                          <div className="text-sm mt-2">
                            <strong>Analysis:</strong>
                            <ul className="list-disc list-inside text-gray-700 mt-1">
                        {report.source_credibility.reasons.map((reason,idx) =>(
                              <li key={idx}>
                                <strong>{reason}</strong>{" "}
                                
                              </li>))
}
                            </ul>
                          </div>
                        
                      </CardContent>
                    </Card>
                  )}

               

                  {/* Reverse Image Search Results */}
                  {report.reverse_img && report.reverse_img.status === "success" && (
                    <Card className="border-l-4 border-red-400 shadow-sm">
                      <CardHeader>
                        <CardTitle className="text-red-600 flex items-center gap-2">
                          <Image className="h-5 w-5" />
                          Reverse Image Search Results
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-5">
                        <p className="text-sm text-muted-foreground">
                          <strong>Article Title:</strong> {report.reverse_img.article_title}
                        </p>

                        {report.reverse_img.image_results.map((img, idx) => (
                          <div
                            key={idx}
                            className="p-4 rounded-lg border bg-purple-50 space-y-3 shadow-sm"
                          >
                            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                              <img
                                src={img.image_url}
                                alt={`Image ${idx + 1}`}
                                className="w-full sm:w-40 h-auto rounded-lg border"
                              />
                              <div>
                                <p className="font-medium text-red-700">
                                  Image {idx + 1} — Top Matches:
                                </p>
                              </div>
                            </div>

                            {/* Best Matches */}
                            <div className="mt-3 space-y-2">
                              {img.best_matches.map((match, j) => (
                                <div
                                  key={j}
                                  className="p-3 border rounded-lg bg-white hover:bg-purple-100 transition"
                                >
                                  <p className="font-medium text-gray-800">
                                    {match.title || "Untitled"}
                                  </p>
                                  <p className="text-sm text-gray-600">
                                    <strong>Source:</strong> {match.source}
                                  </p>
                                  <p className="text-sm text-gray-600">
                                    <strong>Category:</strong> {match.category}
                                  </p>
                                  <p className="text-sm text-gray-600">
                                    <strong>Score:</strong> {(match.score * 100).toFixed(0)}%
                                  </p>
                                  <a
                                    href={match.link}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-sm text-blue-600 hover:underline break-all"
                                  >
                                    {match.link}
                                  </a>
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  )}


                </motion.div>
              )}
            </AnimatePresence>
          </div>
          <div className="space-y-6">
          {/* RIGHT COLUMN - Lottie & Info (Only show when NOT analyzing and NO report) */}
          <AnimatePresence>
            {!report && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="space-y-6"
              >
                {/* Lottie Animation */}
                <Card className="shadow-lg border border-blue-100">
                  <CardContent className="p-6">
                    <div className="text-center space-y-4">
                      <Lottie
                        animationData={analysisAnimation}
                        loop={true}
                        style={{height:'17rem'}}
                      />
                      <div className="space-y-2">
                        {/* <h3 className="font-semibold text-gray-800">
                          How It Works
                        </h3> */}
                        <h3 className="text-med text-gray-600">
                          Our AI analyzes content across multiple dimensions to provide comprehensive credibility assessment
                        </h3>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                
                {/* Article Info Placeholder */}
                <Card className="shadow-lg border border-blue-100">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-blue-600">
                      <Globe className="h-5 w-5" />
                      Article Information
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 text-center py-4">
                      Submit a URL, text, or file to see detailed analysis results here.
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>

          {/* RIGHT COLUMN - Article Info when report exists */}
          <AnimatePresence>
            {report && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="space-y-6"
              >
                {/* Article Info */}
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
                    <p className="text-sm text-muted-foreground break-all">
                      <strong>Title:</strong> {report.title}
                    </p>
                    <p className="text-sm mt-1 flex items-center gap-2">
                      <Globe className="w-4 h-4 text-blue-500" />
                      <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">
                        {report.lang.toUpperCase()}
                      </span>
                    </p>
                  </CardContent>
                </Card>
                 {/* Cross Verify Results */}
                  {report.cross_verify && (
                    <Card className="border-l-4 border-purple-500 shadow-lg">
                      <CardHeader>
                        <CardTitle className="text-purple-600 flex items-center gap-2">
                          <Globe className="h-5 w-5" />
                          Cross Verification Results
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm text-gray-700">
                          <p><strong>Article:</strong> {report.cross_verify.article.title}</p>
                          <p><strong>Source:</strong> {report.cross_verify.article.source}</p>
                          <p>
                            <strong>Verdict:</strong>{" "}
                            <span
                              className={`font-medium ${
                                report.cross_verify.verification.verdict === "HIGHLY_CREDIBLE"
                                  ? "text-green-600"
                                  : report.cross_verify.verification.verdict === "UNVERIFIED"
                                  ? "text-yellow-600"
                                  : "text-red-600"
                              }`}
                            >
                              {report.cross_verify.verification.verdict}
                            </span>
                          </p>
                          <p>
                            <strong>Confidence:</strong>{" "}
                            {(report.cross_verify.verification.confidence * 100).toFixed(0)}%
                          </p>
                          <p>
                            <strong>Credibility Score:</strong>{" "}
                            {(report.cross_verify.verification.credibility_score * 100).toFixed(0)}%
                          </p>
                          <p>
                            <strong>Consensus:</strong> {report.cross_verify.consensus_analysis.analysis}
                          </p>
                          <p>
                            <strong>Sources Analyzed:</strong> {report.cross_verify.consensus_analysis.total_sources}
                          </p>
                          <p>
                            <strong>Confirmations:</strong> {report.cross_verify.consensus_analysis.confirmations?.length || 0}
                          </p>
                          <p>
                            <strong>Contradictions:</strong> {report.cross_verify.consensus_analysis.contradictions?.length || 0}
                          </p>
                        </div>

                        <div className="border-t border-gray-300 my-2"></div>

                        {/* Top Confirmations */}
                        <div>
                          <h3 className="text-sm font-semibold text-gray-800 mb-2">✅ Top Confirmations:</h3>
                          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                            {report.cross_verify.consensus_analysis.confirmations?.slice(0, 3).map((conf, idx) => (
                              <li key={idx}>
                                <b>{conf.source}:</b> {conf.title.slice(0, 85)}...
                              </li>
                            )) || <li>No confirmations available</li>}
                          </ul>
                        </div>

                        <div className="border-t border-gray-300 my-2"></div>

                        {/* Related Articles */}
                        <div>
                          <h3 className="text-sm font-semibold text-gray-800 mb-2">📰 Related Articles:</h3>
                          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                            {report.cross_verify.similar_articles?.slice(0, 3).map((art, idx) => (
                              <li key={idx}>
                                <a
                                  href={art.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-600 hover:underline"
                                >
                                  {art.title.slice(0, 80)}...
                                </a>{" "}
                                <span className="text-gray-500">({art.source})</span>
                              </li>
                            )) || <li>No similar articles found</li>}
                          </ul>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                  
                  {/* Flagged Phrases */}
                  {report.trigger_report?.list_of_phrases && (
                    <Card className="border-l-4 border-yellow-400 shadow-sm">
                      <CardHeader>
                        <CardTitle className="text-yellow-600 flex items-center gap-2">
                          🚩 Flagged Phrases
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {report.trigger_report.list_of_phrases.map((t, i) => (
                          <div key={i} className="p-3 border rounded-lg bg-yellow-50">
                            <p className="font-medium">"{t.phrase}"</p>
                            <p className="text-sm italic text-muted-foreground mt-1">
                              ...{t.snippet}...
                            </p>
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  )}
                {/* Additional analysis info can go here */}
              </motion.div>
            )}
            
                 
          </AnimatePresence>
          </div>
          {/* {report && */}
           
          {/* } */}
        </div>
       {report && <div>
        {report.final_risk_assessment && (
  <Card className={`border-l-4 ${getFinalRiskBorderColor(report.final_risk_assessment.risk_score)} shadow-lg`}>
    <CardHeader>
      <CardTitle className={`${getFinalRiskTextColor(report.final_risk_assessment.risk_score)} flex items-center gap-2`}>
        {getFinalRiskIcon(report.final_risk_assessment.risk_score)}
        Final Risk Assessment
      </CardTitle>
    </CardHeader>
    <CardContent className="space-y-4">
      {/* Main Risk Score */}
      <div className="flex items-center gap-6">
        <div className="relative">
          <div className="w-20 h-20 rounded-full border-4 border-gray-200 flex items-center justify-center">
            <div
              className={`w-16 h-16 rounded-full ${getFinalRiskColor(report.final_risk_assessment.risk_score)} flex items-center justify-center text-white font-bold`}
            >
              {(report.final_risk_assessment.risk_score * 100).toFixed(0)}%
            </div>
          </div>
        </div>
        
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className={`text-2xl font-bold ${getFinalRiskTextColor(report.final_risk_assessment.risk_score)}`}>
              {report.final_risk_assessment.final_verdict.replace(/[⚠️✅🚨]/g, '').trim()}
            </span>
            <Badge className={getFinalRiskBadgeColor(report.final_risk_assessment.risk_score)}>
              {getFinalRiskLevel(report.final_risk_assessment.risk_score)}
            </Badge>
          </div>
          
          <p className="text-sm text-gray-600">
            {report.final_risk_assessment.statement}
          </p>
        </div>
      </div>

      {/* Risk Breakdown */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-600">Source Credibility</span>
            <span className="font-medium">{((report.final_risk_assessment.breakdown.source_credibility_score) * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-green-500 h-2 rounded-full" 
              style={{ width: `${(report.final_risk_assessment.breakdown.source_credibility_score) * 100}%` }}
            ></div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-600">Content Risk</span>
            <span className="font-medium">{(report.final_risk_assessment.breakdown.content_risk_score * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-red-500 h-2 rounded-full" 
              style={{ width: `${report.final_risk_assessment.breakdown.content_risk_score * 100}%` }}
            ></div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-600">Verification</span>
            <span className="font-medium">{((report.final_risk_assessment.breakdown.verification_confidence) * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full" 
              style={{ width: `${(report.final_risk_assessment.breakdown.verification_confidence) * 100}%` }}
            ></div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-600">Image Check</span>
            <span className="font-medium">{((report.final_risk_assessment.breakdown.image_consistency_score) * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-purple-500 h-2 rounded-full" 
              style={{ width: `${(report.final_risk_assessment.breakdown.image_consistency_score) * 100}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Additional Context */}
      <div className="flex items-center justify-between text-xs text-gray-500 border-t pt-3">
        <span>🚩 {report.final_risk_assessment.additional_context.flagged_phrases_count} flagged phrases</span>
        <span>📊 {report.final_risk_assessment.additional_context.cross_verification_sources} sources checked</span>
        <span>🖼️ {report.final_risk_assessment.additional_context.image_verification_status}</span>
      </div>
    </CardContent>
  </Card>
)}
</div>}
      </motion.div>
    </PageLayout>
  );
}