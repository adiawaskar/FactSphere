import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { PageLayout } from '@/components/layout/PageLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Globe, 
  RefreshCw, 
  AlertTriangle, 
  TrendingUp, 
  Shield,
  X,
  Check,
  Brain,
  FileText,
  Download,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Link as LinkIcon
} from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

interface TrendData {
  success: boolean;
  timestamp: string;
  analysis?: string;
  trends?: Array<{
    topic: string;
    risk_level: 'low' | 'medium' | 'high';
    misinformation_score: number;
    confidence: number;
    article_count: number;
    justification: string;
    sources?: Array<{
      title: string;
      url: string;
      domain: string;
      snippet: string;
      is_credible: boolean;
      is_problematic: boolean;
      credibility_score: number;
    }>;
    cross_verification?: {
      contradiction_count: number;
      consistency_score: number;
      contradictions?: Record<string, string>;
    };
    gemini_analysis?: string;
    recommendations?: string[];
    verification_sources?: string[];
    metrics?: {
      credibility_score: number;
      confidence: number;
      emotional_language: number;
      source_reliability: number;
      factual_consistency?: number;
      source_diversity?: number;
      global_spread_risk?: number;
    };
  }>;
  metrics_summary?: {
    topics_analyzed: number;
    high_risk_percentage: number;
    overall_confidence: number;
    total_contradictions: number;
    analysis_timestamp: string;
    top_misinformation_indicators: Array<{name: string; count: number}>;
    top_credibility_indicators: Array<{name: string; count: number}>;
  };
  using_gemini?: boolean;
}

export default function GlobalTrends() {
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<TrendData | null>(null);
  const [expandedTrends, setExpandedTrends] = useState<Set<number>>(new Set());

  const fetchData = async () => {
    try {
      const response = await axios.get<TrendData>('http://127.0.0.1:8000/api/agent/results');
      setData(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load data");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await axios.post('http://127.0.0.1:8000/api/agent/analyze');
      await new Promise(resolve => setTimeout(resolve, 3000));
      await fetchData();
    } catch (err: any) {
      setError(err.message || "Failed to refresh data");
    } finally {
      setIsRefreshing(false);
    }
  };

  const generateReport = () => {
    if (!data || !data.trends) return;
    
    const report = `
Global Misinformation Report - ${new Date().toLocaleString()}
${'='.repeat(60)}

${data.analysis}

TRENDS ANALYZED: ${data.trends.length}

${data.trends.map((trend, i) => `
${i + 1}. ${trend.topic}
   Risk Level: ${trend.risk_level.toUpperCase()}
   Misinformation Score: ${(trend.misinformation_score * 100).toFixed(1)}%
   Confidence: ${(trend.confidence * 100).toFixed(1)}%
   Sources: ${trend.article_count}
   Contradictions: ${trend.cross_verification?.contradiction_count || 0}
`).join('\n')}
`;

    const blob = new Blob([report], {type: 'text/plain'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `global-misinfo-report-${new Date().toISOString().slice(0,10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const toggleTrend = (index: number) => {
    setExpandedTrends(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  if (isLoading) {
    return (
      <PageLayout>
        <div className="flex flex-col items-center justify-center min-h-[50vh]">
          <RefreshCw className="h-10 w-10 animate-spin text-primary mb-4" />
          <h2 className="text-xl font-medium">Loading Global Misinformation Monitor...</h2>
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout>
      <div className="py-8 space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full">
            <Globe className="h-5 w-5 text-primary" />
            <span className="text-primary font-medium">Global Misinformation Monitor</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold">Worldwide Fact Tracking</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Real-time monitoring and cross-verification of misinformation spreading globally
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* No Data State */}
        {!data && !error && (
          <Card>
            <CardContent className="py-12 text-center">
              <Globe className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-xl font-medium mb-2">No Analysis Available</h3>
              <p className="text-muted-foreground mb-6">
                Start monitoring worldwide misinformation trends
              </p>
              <Button onClick={handleRefresh} disabled={isRefreshing}>
                {isRefreshing ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Globe className="h-4 w-4 mr-2" />
                    Run Global Analysis
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Main Content */}
        {data && (
          <Tabs defaultValue="dashboard" className="space-y-6">
            <div className="flex justify-between items-center">
              <TabsList>
                <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
                <TabsTrigger value="trends">Trends</TabsTrigger>
                <TabsTrigger value="indicators">Indicators</TabsTrigger>
              </TabsList>
              
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={generateReport}>
                  <Download className="h-4 w-4 mr-2" />
                  Report
                </Button>
                <Button size="sm" onClick={handleRefresh} disabled={isRefreshing}>
                  {isRefreshing ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Refresh
                    </>
                  )}
                </Button>
              </div>
            </div>

            {/* Dashboard Tab */}
            <TabsContent value="dashboard" className="space-y-6">
              {data.metrics_summary && (
                <>
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Topics Analyzed</CardTitle>
                        <Globe className="h-4 w-4 text-muted-foreground" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{data.metrics_summary.topics_analyzed}</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">High Risk</CardTitle>
                        <AlertTriangle className="h-4 w-4 text-red-500" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-red-500">
                          {Math.round(data.metrics_summary.high_risk_percentage)}%
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Contradictions</CardTitle>
                        <X className="h-4 w-4 text-yellow-500" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{data.metrics_summary.total_contradictions}</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Confidence</CardTitle>
                        <Shield className="h-4 w-4 text-primary" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {Math.round(data.metrics_summary.overall_confidence * 100)}%
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle>Analysis Summary</CardTitle>
                      <CardDescription>
                        Last updated: {new Date(data.metrics_summary.analysis_timestamp).toLocaleString()}
                        {data.using_gemini && (
                          <Badge variant="outline" className="ml-2">
                            <Brain className="h-3 w-3 mr-1" />
                            Enhanced with Gemini API
                          </Badge>
                        )}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm whitespace-pre-line">{data.analysis}</p>
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>

            {/* Trends Tab */}
            <TabsContent value="trends" className="space-y-4">
              {data.trends && data.trends.map((trend, index) => (
                <Card key={index}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div className="space-y-1 flex-1">
                        <CardTitle className="text-lg">{trend.topic}</CardTitle>
                        <CardDescription>
                          {trend.sources?.length || trend.article_count} sources • 
                          {trend.cross_verification?.contradiction_count || 0} contradictions
                        </CardDescription>
                      </div>
                      <Badge className={getRiskColor(trend.risk_level)}>
                        {trend.risk_level.toUpperCase()}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Misinformation Risk</span>
                        <span className="font-medium">
                          {Math.round(trend.misinformation_score * 100)}%
                        </span>
                      </div>
                      <Progress value={trend.misinformation_score * 100} />
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Analysis Confidence</span>
                        <span className="font-medium">
                          {Math.round(trend.confidence * 100)}%
                        </span>
                      </div>
                      <Progress value={trend.confidence * 100} />
                    </div>

                    {/* Additional Metrics */}
                    {trend.metrics && (
                      <div className="grid grid-cols-2 gap-2 pt-2">
                        {trend.metrics.factual_consistency !== undefined && (
                          <div className="text-sm">
                            <span className="text-muted-foreground">Factual Consistency: </span>
                            <span className="font-medium">{Math.round(trend.metrics.factual_consistency * 100)}%</span>
                          </div>
                        )}
                        {trend.metrics.source_diversity !== undefined && (
                          <div className="text-sm">
                            <span className="text-muted-foreground">Source Diversity: </span>
                            <span className="font-medium">{Math.round(trend.metrics.source_diversity * 100)}%</span>
                          </div>
                        )}
                        {trend.metrics.emotional_language !== undefined && (
                          <div className="text-sm">
                            <span className="text-muted-foreground">Emotional Language: </span>
                            <span className="font-medium">{Math.round(trend.metrics.emotional_language * 100)}%</span>
                          </div>
                        )}
                        {trend.metrics.source_reliability !== undefined && (
                          <div className="text-sm">
                            <span className="text-muted-foreground">Source Reliability: </span>
                            <span className="font-medium">{Math.round(trend.metrics.source_reliability * 100)}%</span>
                          </div>
                        )}
                      </div>
                    )}

                    <p className="text-sm text-muted-foreground">{trend.justification}</p>

                    {/* Comprehensive Analysis Section */}
                    <Collapsible
                      open={expandedTrends.has(index)}
                      onOpenChange={() => toggleTrend(index)}
                    >
                      <CollapsibleTrigger asChild>
                        <Button variant="outline" size="sm" className="w-full">
                          {expandedTrends.has(index) ? (
                            <>
                              <ChevronUp className="h-4 w-4 mr-2" />
                              Hide Detailed Analysis
                            </>
                          ) : (
                            <>
                              <ChevronDown className="h-4 w-4 mr-2" />
                              Show Detailed Analysis & Sources
                            </>
                          )}
                        </Button>
                      </CollapsibleTrigger>
                      <CollapsibleContent className="space-y-4 pt-4">
                        {/* Sources Section */}
                        {trend.sources && trend.sources.length > 0 && (
                          <div className="space-y-3">
                            <h4 className="font-semibold flex items-center gap-2">
                              <LinkIcon className="h-4 w-4" />
                              Sources Analyzed ({trend.sources.length})
                            </h4>
                            <div className="space-y-2">
                              {trend.sources.map((source, sourceIndex) => (
                                <div
                                  key={sourceIndex}
                                  className="border rounded-lg p-3 space-y-2"
                                >
                                  <div className="flex items-start justify-between gap-2">
                                    <div className="flex-1 min-w-0">
                                      <a
                                        href={source.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="font-medium text-sm hover:underline flex items-center gap-1"
                                      >
                                        {source.title}
                                        <ExternalLink className="h-3 w-3" />
                                      </a>
                                      <p className="text-xs text-muted-foreground mt-1">
                                        {source.domain}
                                      </p>
                                    </div>
                                    <div className="flex gap-1">
                                      {source.is_credible && (
                                        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                                          <Check className="h-3 w-3 mr-1" />
                                          Credible
                                        </Badge>
                                      )}
                                      {source.is_problematic && (
                                        <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
                                          <AlertTriangle className="h-3 w-3 mr-1" />
                                          Caution
                                        </Badge>
                                      )}
                                    </div>
                                  </div>
                                  <p className="text-xs text-muted-foreground">
                                    {source.snippet}
                                  </p>
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs text-muted-foreground">
                                      Credibility:
                                    </span>
                                    <Progress
                                      value={source.credibility_score * 100}
                                      className="h-1 flex-1"
                                    />
                                    <span className="text-xs font-medium">
                                      {Math.round(source.credibility_score * 100)}%
                                    </span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Gemini AI Analysis */}
                        {trend.gemini_analysis && (
                          <div className="space-y-2">
                            <h4 className="font-semibold flex items-center gap-2">
                              <Brain className="h-4 w-4 text-primary" />
                              AI Comprehensive Analysis
                            </h4>
                            <div className="bg-muted/50 rounded-lg p-4">
                              <p className="text-sm whitespace-pre-wrap">
                                {trend.gemini_analysis}
                              </p>
                            </div>
                          </div>
                        )}

                        {/* Contradictions */}
                        {trend.cross_verification?.contradictions && 
                         Object.keys(trend.cross_verification.contradictions).length > 0 && (
                          <div className="space-y-2">
                            <h4 className="font-semibold flex items-center gap-2 text-yellow-700">
                              <X className="h-4 w-4" />
                              Source Contradictions
                            </h4>
                            <div className="space-y-2">
                              {Object.entries(trend.cross_verification.contradictions).map(
                                ([sources, description], idx) => (
                                  <Alert key={idx} variant="default" className="border-yellow-200">
                                    <AlertTriangle className="h-4 w-4 text-yellow-600" />
                                    <AlertTitle className="text-sm">
                                      {sources}
                                    </AlertTitle>
                                    <AlertDescription className="text-xs">
                                      {description}
                                    </AlertDescription>
                                  </Alert>
                                )
                              )}
                            </div>
                          </div>
                        )}

                        {/* Recommendations */}
                        {trend.recommendations && trend.recommendations.length > 0 && (
                          <div className="space-y-2">
                            <h4 className="font-semibold flex items-center gap-2">
                              <Shield className="h-4 w-4 text-primary" />
                              Recommendations
                            </h4>
                            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                              {trend.recommendations.map((rec, idx) => (
                                <li key={idx}>{rec}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Verification Sources */}
                        {trend.verification_sources && trend.verification_sources.length > 0 && (
                          <div className="space-y-2">
                            <h4 className="font-semibold flex items-center gap-2">
                              <Check className="h-4 w-4 text-green-600" />
                              Suggested Verification Sources
                            </h4>
                            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                              {trend.verification_sources.map((source, idx) => (
                                <li key={idx}>{source}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </CollapsibleContent>
                    </Collapsible>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>

            {/* Indicators Tab */}
            <TabsContent value="indicators" className="space-y-6">
              {data.metrics_summary && (
                <div className="grid gap-6 md:grid-cols-2">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <X className="h-5 w-5 text-red-500" />
                        Top Misinformation Indicators
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {data.metrics_summary.top_misinformation_indicators?.slice(0, 5).map((indicator, i) => (
                          <div key={i} className="flex justify-between items-center">
                            <span className="text-sm">{indicator.name}</span>
                            <Badge variant="outline">{indicator.count}</Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Check className="h-5 w-5 text-green-500" />
                        Top Credibility Indicators
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {data.metrics_summary.top_credibility_indicators?.slice(0, 5).map((indicator, i) => (
                          <div key={i} className="flex justify-between items-center">
                            <span className="text-sm">{indicator.name}</span>
                            <Badge variant="outline">{indicator.count}</Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
            </TabsContent>
          </Tabs>
        )}
      </div>
    </PageLayout>
  );
}
