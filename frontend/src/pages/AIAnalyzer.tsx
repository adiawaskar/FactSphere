
import { useState } from 'react';
import { PageLayout } from '@/components/layout/PageLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Bot, Send, Upload, Link, Type, Loader2, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useInView } from 'react-intersection-observer';

interface AnalysisResult {
  verdict: 'true' | 'false' | 'partial' | 'unverified';
  confidence: number;
  sources: Array<{
    title: string;
    url: string;
    credibility: number;
  }>;
  reasoning: string;
  factChecks: Array<{
    claim: string;
    status: 'verified' | 'disputed' | 'false';
    explanation: string;
  }>;
}

export default function AIAnalyzer() {
  const [activeTab, setActiveTab] = useState('text');
  const [textInput, setTextInput] = useState('');
  const [urlInput, setUrlInput] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const handleAnalyze = async () => {
    if (!textInput && !urlInput) return;
    
    setIsAnalyzing(true);
    
    // Simulate AI analysis
    await new Promise(resolve => setTimeout(resolve, 4000));
    
    // Mock result
    const mockResult: AnalysisResult = {
      verdict: Math.random() > 0.7 ? 'true' : Math.random() > 0.4 ? 'false' : 'partial',
      confidence: 70 + Math.random() * 30,
      sources: [
        { title: 'Reuters Fact Check', url: 'https://reuters.com', credibility: 95 },
        { title: 'Associated Press', url: 'https://ap.org', credibility: 92 },
        { title: 'Snopes', url: 'https://snopes.com', credibility: 88 }
      ],
      reasoning: 'Based on cross-referencing with multiple credible sources and fact-checking databases, the claim contains elements that have been verified by reputable news organizations.',
      factChecks: [
        { claim: 'Main assertion', status: 'verified', explanation: 'Confirmed by multiple sources' },
        { claim: 'Supporting detail', status: 'disputed', explanation: 'Some conflicting information found' }
      ]
    };
    
    setResult(mockResult);
    setIsAnalyzing(false);
  };

  const getVerdictIcon = (verdict: string) => {
    switch (verdict) {
      case 'true': return <CheckCircle className="h-5 w-5 text-verified" />;
      case 'false': return <XCircle className="h-5 w-5 text-danger" />;
      case 'partial': return <AlertTriangle className="h-5 w-5 text-warning" />;
      default: return <AlertTriangle className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getVerdictColor = (verdict: string) => {
    switch (verdict) {
      case 'true': return 'text-verified bg-verified/10';
      case 'false': return 'text-danger bg-danger/10';
      case 'partial': return 'text-warning bg-warning/10';
      default: return 'text-muted-foreground bg-muted/10';
    }
  };

  return (
    <PageLayout className="py-8">
      <motion.div
        ref={ref}
        initial={{ opacity: 0, y: 50 }}
        animate={inView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.6 }}
        className="space-y-8"
      >
        {/* Hero Section */}
        <div className="text-center space-y-4">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            className="inline-flex items-center gap-2 px-4 py-2 bg-secondary/10 rounded-full"
          >
            <Bot className="h-5 w-5 text-secondary" />
            <span className="text-secondary font-medium">AI-Powered Analysis</span>
          </motion.div>
          
          <motion.h1 
            className="text-4xl md:text-6xl font-bold text-gradient"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            AI Fact Checker
          </motion.h1>
          
          <motion.p 
            className="text-xl text-muted-foreground max-w-2xl mx-auto"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            Submit any claim, article, or media content for comprehensive AI-powered fact-checking and verification
          </motion.p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input Section */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Type className="h-5 w-5" />
                  Submit for Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="text">Text</TabsTrigger>
                    <TabsTrigger value="url">URL</TabsTrigger>
                    <TabsTrigger value="file">File</TabsTrigger>
                  </TabsList>

                  <div className="mt-6">
                    <TabsContent value="text" className="space-y-4">
                      <Textarea
                        placeholder="Paste the claim, news article, or statement you want to fact-check..."
                        value={textInput}
                        onChange={(e) => setTextInput(e.target.value)}
                        className="min-h-40 resize-none"
                      />
                    </TabsContent>

                    <TabsContent value="url" className="space-y-4">
                      <Input
                        type="url"
                        placeholder="https://example.com/article-to-verify"
                        value={urlInput}
                        onChange={(e) => setUrlInput(e.target.value)}
                      />
                    </TabsContent>

                    <TabsContent value="file" className="space-y-4">
                      <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center">
                        <Upload className="h-8 w-8 mx-auto mb-4 text-muted-foreground" />
                        <p className="text-muted-foreground">Upload documents or images</p>
                      </div>
                    </TabsContent>

                    <Button
                      onClick={handleAnalyze}
                      disabled={isAnalyzing || (!textInput && !urlInput)}
                      className="w-full gradient-primary mt-6"
                    >
                      {isAnalyzing ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Analyzing...
                        </>
                      ) : (
                        <>
                          <Send className="mr-2 h-4 w-4" />
                          Analyze Content
                        </>
                      )}
                    </Button>
                  </div>
                </Tabs>
              </CardContent>
            </Card>
          </motion.div>

          {/* Results Section */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
          >
            <Card className="glass-card h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bot className="h-5 w-5" />
                  Analysis Results
                </CardTitle>
              </CardHeader>
              <CardContent>
                <AnimatePresence mode="wait">
                  {!result && !isAnalyzing && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex items-center justify-center h-64 text-muted-foreground"
                    >
                      Submit content to see analysis results
                    </motion.div>
                  )}

                  {isAnalyzing && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex flex-col items-center justify-center h-64 space-y-4"
                    >
                      <Loader2 className="h-8 w-8 animate-spin text-primary" />
                      <p className="text-muted-foreground">AI is analyzing the content...</p>
                    </motion.div>
                  )}

                  {result && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="space-y-6"
                    >
                      <div className="flex items-center gap-3">
                        {getVerdictIcon(result.verdict)}
                        <div>
                          <h3 className="text-lg font-semibold flex items-center gap-2">
                            <Badge className={getVerdictColor(result.verdict)}>
                              {result.verdict.toUpperCase()}
                            </Badge>
                          </h3>
                          <p className="text-sm text-muted-foreground">
                            Confidence: {result.confidence.toFixed(1)}%
                          </p>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h4 className="font-medium">AI Reasoning</h4>
                        <p className="text-sm text-muted-foreground p-4 bg-muted/50 rounded-lg">
                          {result.reasoning}
                        </p>
                      </div>

                      <div className="space-y-4">
                        <h4 className="font-medium">Fact Checks</h4>
                        {result.factChecks.map((check, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="p-3 border rounded-lg space-y-2"
                          >
                            <div className="flex items-center gap-2">
                              <Badge
                                className={
                                  check.status === 'verified' ? 'bg-verified/10 text-verified' :
                                  check.status === 'disputed' ? 'bg-warning/10 text-warning' :
                                  'bg-danger/10 text-danger'
                                }
                              >
                                {check.status}
                              </Badge>
                              <span className="text-sm font-medium">{check.claim}</span>
                            </div>
                            <p className="text-xs text-muted-foreground">{check.explanation}</p>
                          </motion.div>
                        ))}
                      </div>

                      <div className="space-y-4">
                        <h4 className="font-medium">Sources</h4>
                        {result.sources.map((source, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="flex items-center justify-between p-2 border rounded"
                          >
                            <div>
                              <p className="text-sm font-medium">{source.title}</p>
                              <p className="text-xs text-muted-foreground">{source.url}</p>
                            </div>
                            <Badge variant="outline">
                              {source.credibility}% credible
                            </Badge>
                          </motion.div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </motion.div>
    </PageLayout>
  );
}
