//frontend/src/pages/SocialTrends.tsx
import { useState, useEffect } from 'react';
import axios from 'axios';
import { PageLayout } from '@/components/layout/PageLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  TrendingUp, AlertTriangle, Twitter, Globe, RefreshCw, Activity, Brain, 
  BarChart2, Facebook, Instagram, PieChart, LineChart, ArrowRight, 
  ArrowUpRight, ArrowDownRight, Gauge, Info, Scale, Check, X, Shield, 
  FileText, BarChart, Share2, MessageCircle, Link2, UserCheck
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useInView } from 'react-intersection-observer';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';

interface TrendItem {
  id: string;
  topic: string;
  platform: 'twitter' | 'facebook' | 'instagram' | 'tiktok';
  mentions: number;
  sentiment: 'positive' | 'negative' | 'neutral';
  misinformationRisk: 'low' | 'medium' | 'high';
  description: string;
  timestamp: string;
}

// Fallback data in case API fails
const mockTrends: TrendItem[] = [
  {
    id: '1',
    topic: 'Climate Change Hoax',
    platform: 'twitter',
    mentions: 45000,
    sentiment: 'negative',
    misinformationRisk: 'high',
    description: 'False claims about climate data manipulation spreading rapidly',
    timestamp: '2 hours ago'
  },
  {
    id: '2',
    topic: 'Vaccine Side Effects',
    platform: 'facebook',
    mentions: 32000,
    sentiment: 'negative',
    misinformationRisk: 'high',
    description: 'Unverified reports linking vaccines to various health issues',
    timestamp: '4 hours ago'
  },
  {
    id: '3',
    topic: 'Election Fraud Claims',
    platform: 'twitter',
    mentions: 28000,
    sentiment: 'neutral',
    misinformationRisk: 'medium',
    description: 'Ongoing discussions about voting system security',
    timestamp: '6 hours ago'
  },
  {
    id: '4',
    topic: 'AI Job Displacement',
    platform: 'instagram',
    mentions: 18000,
    sentiment: 'negative',
    misinformationRisk: 'low',
    description: 'Concerns about AI replacing human workers',
    timestamp: '8 hours ago'
  }
];

interface AgentStatus {
  available: boolean;
  running: boolean;
  last_run: string | null;
  gemini_api_available?: boolean;
}

interface AgentAnalysis {
  success: boolean;
  timestamp: string;
  analysis?: string;
  trends?: any[];
  metrics_summary?: any;
  error?: string;
  using_gemini?: boolean;
}

// Helper function to format numbers
const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
};

// Helper to get color based on risk level
const getRiskColorClass = (risk: string) => {
  switch (risk) {
    case 'high': return 'text-danger bg-danger/10';
    case 'medium': return 'text-warning bg-warning/10';
    case 'low': return 'text-verified bg-verified/10';
    default: return 'text-muted-foreground bg-muted/10';
  }
};

// Helper to get sentiment icon
const getSentimentIcon = (sentiment: string) => {
  switch (sentiment) {
    case 'positive': return <ArrowUpRight className="text-verified" />;
    case 'negative': return <ArrowDownRight className="text-danger" />;
    default: return <ArrowRight className="text-muted-foreground" />;
  }
};

export default function SocialTrends() {
  const [trends, setTrends] = useState<TrendItem[]>(mockTrends);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('trends');
  const [activeDashboardTab, setActiveDashboardTab] = useState<string>('overview');
  
  // Agent-related state
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [agentResults, setAgentResults] = useState<AgentAnalysis | null>(null);
  const [isAgentRefreshing, setIsAgentRefreshing] = useState(false);
  const [agentError, setAgentError] = useState<string | null>(null);
  
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const fetchTrends = async () => {
    setIsRefreshing(true);
    setError(null);
    
    try {
      console.log("Fetching trends from backend API...");
      // Update the URL to point to the backend API
      const response = await axios.get('http://127.0.0.1:8000/api/trends');
      
      console.log("API response received:", response.data);
      
      if (response.data.success) {
        // Map API response to match TrendItem interface
        const mappedTrends: TrendItem[] = response.data.trends.map((trend: any, index: number) => ({
          id: String(index + 1),
          topic: trend.topic || 'Unknown Topic',
          platform: trend.platform || 'twitter',
          mentions: trend.frequency || trend.mentions || 0,
          sentiment: trend.sentiment || 'neutral',
          misinformationRisk: trend.severity || trend.misinformationRisk || 'medium',
          description: trend.description || 'No description available',
          timestamp: trend.timestamp || 'Recently'
        }));
        
        console.log(`Mapped ${mappedTrends.length} trends from API response`);
        setTrends(mappedTrends);
      } else {
        console.error("API returned success: false");
        setError('Failed to fetch trends data');
        // Keep using mock data if API fails
      }
    } catch (error: any) {
      console.error('Error fetching trends:', error);
      // Add more detailed error logging
      if (error.response) {
        console.error('Response error data:', error.response.data);
        console.error('Response error status:', error.response.status);
      } else if (error.request) {
        console.error('No response received:', error.request);
      } else {
        console.error('Error message:', error.message);
      }
      
      setError(`Error connecting to the server: ${error.message || 'Unknown error'}`);
      // Keep using mock data if API fails
    } finally {
      setIsRefreshing(false);
    }
  };

  const fetchAgentStatus = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/api/agent/status');
      setAgentStatus(response.data);
    } catch (error: any) {
      console.error('Error fetching agent status:', error);
      setAgentStatus({
        available: false,
        running: false,
        last_run: null
      });
    }
  };

  const fetchAgentResults = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/api/agent/results');
      setAgentResults(response.data);
      setAgentError(null);
      
      // Auto-switch to overview tab when results are loaded
      if (response.data && response.data.success && !response.data.error) {
        setActiveDashboardTab('overview');
      }
    } catch (error: any) {
      console.error('Error fetching agent results:', error);
      setAgentError('Could not load agent analysis results');
    }
  };

  const triggerAgentAnalysis = async () => {
    setIsAgentRefreshing(true);
    setAgentError(null);
    
    try {
      await axios.post('http://127.0.0.1:8000/api/agent/analyze');
      
      // Poll for status
      const checkStatus = async () => {
        const status = await axios.get('http://127.0.0.1:8000/api/agent/status');
        setAgentStatus(status.data);
        
        if (status.data.running) {
          // Still running, check again in 3 seconds
          setTimeout(checkStatus, 3000);
        } else {
          // Finished, get results
          fetchAgentResults();
          setIsAgentRefreshing(false);
        }
      };
      
      // Start polling
      setTimeout(checkStatus, 3000);
      
    } catch (error: any) {
      console.error('Error triggering agent analysis:', error);
      setAgentError('Failed to start agent analysis');
      setIsAgentRefreshing(false);
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchTrends();
    fetchAgentStatus();
    fetchAgentResults();
    
    // Auto-refresh every 5 minutes
    const intervalId = setInterval(fetchTrends, 5 * 60 * 1000);
    return () => clearInterval(intervalId);
  }, []);

  const handleRefresh = () => {
    fetchTrends();
  };

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case 'twitter': return <Twitter className="h-4 w-4" />;
      case 'facebook': return <Facebook className="h-4 w-4" />;
      case 'instagram': return <Instagram className="h-4 w-4" />;
      default: return <Globe className="h-4 w-4" />;
    }
  };

  const filteredTrends = selectedPlatform === 'all' 
    ? trends 
    : trends.filter(trend => trend.platform === selectedPlatform);

  const renderMetricCard = (title: string, value: string | number, icon: React.ReactNode, description?: string) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && <p className="text-xs text-muted-foreground mt-1">{description}</p>}
      </CardContent>
    </Card>
  );

  const renderRiskGauge = (score: number, label: string) => {
    const rotation = score * 180; // 0-1 to 0-180 degrees
    const color = score > 0.7 ? "text-danger" : score > 0.4 ? "text-warning" : "text-verified";
    
    return (
      <div className="relative flex flex-col items-center">
        <div className="relative w-24 h-12 overflow-hidden">
          <div className="absolute w-24 h-24 rounded-full border-8 border-muted top-0"></div>
          <motion.div 
            className={`absolute w-1 h-12 bg-foreground left-[3rem] -translate-x-1/2 origin-bottom ${color}`}
            initial={{ rotate: 0 }}
            animate={{ rotate: rotation }}
            transition={{ duration: 1 }}
          />
        </div>
        <div className="mt-1 text-sm font-medium">{label}</div>
        <div className="text-lg font-bold">{Math.round(score * 100)}%</div>
      </div>
    );
  };

  const renderAgentDashboard = () => {
    if (!agentResults || !agentResults.metrics_summary) {
      return (
        <div className="text-center py-8">
          <p className="text-muted-foreground">No metrics available yet. Run an analysis first.</p>
        </div>
      );
    }
    
    const metrics = agentResults.metrics_summary;
    
    return (
      <div className="space-y-6">
        <Tabs defaultValue="overview" value={activeDashboardTab} onValueChange={setActiveDashboardTab}>
          <TabsList className="grid grid-cols-3 w-full max-w-xl mx-auto">
            <TabsTrigger value="overview">
              <PieChart className="h-4 w-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="topics">
              <BarChart className="h-4 w-4 mr-2" />
              Topic Analysis
            </TabsTrigger>
            <TabsTrigger value="indicators">
              <Activity className="h-4 w-4 mr-2" />
              Key Indicators
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="pt-6">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {renderMetricCard(
                "Topics Analyzed", 
                metrics.topics_analyzed, 
                <FileText className="h-4 w-4 text-muted-foreground" />
              )}
              
              {renderMetricCard(
                "High Risk Topics", 
                `${Math.round(metrics.high_risk_percentage)}%`, 
                <AlertTriangle className="h-4 w-4 text-danger" />,
                "Percentage of topics with high misinformation risk"
              )}
              
              {renderMetricCard(
                "Overall Confidence", 
                `${Math.round(metrics.overall_confidence * 100)}%`, 
                <Shield className="h-4 w-4 text-primary" />,
                "Confidence level in the analysis results"
              )}
              
              {renderMetricCard(
                "Sentiment Balance", 
                `${metrics.sentiment_distribution.positive}/${metrics.sentiment_distribution.neutral}/${metrics.sentiment_distribution.negative}`, 
                <Scale className="h-4 w-4 text-muted-foreground" />,
                "Positive/Neutral/Negative distribution"
              )}
            </div>
            
            <div className="mt-8 grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Misinformation Risk Assessment</CardTitle>
                  <CardDescription>Overall risk level across analyzed topics</CardDescription>
                </CardHeader>
                <CardContent className="flex justify-center py-4">
                  <div className="flex flex-col items-center">
                    {renderRiskGauge(metrics.average_misinformation_score, "Average Risk")}
                    <div className="flex justify-between w-full mt-2 text-xs px-6">
                      <span className="text-verified">Low</span>
                      <span className="text-warning">Medium</span>
                      <span className="text-danger">High</span>
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="text-sm text-muted-foreground">
                  Based on {metrics.topics_analyzed} topics analyzed on {new Date(metrics.analysis_timestamp).toLocaleDateString()}
                </CardFooter>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Analysis Insights</CardTitle>
                  <CardDescription>Key findings from the AI analysis</CardDescription>
                </CardHeader>
                <CardContent className="h-[180px] overflow-auto">
                  <ScrollArea className="h-full w-full pr-4">
                    <p className="text-sm whitespace-pre-line">{agentResults.analysis}</p>
                  </ScrollArea>
                </CardContent>
                <CardFooter>
                  {agentResults.using_gemini && (
                    <Badge variant="outline" className="gap-1">
                      <Brain className="h-3 w-3" />
                      Enhanced with Gemini API
                    </Badge>
                  )}
                </CardFooter>
              </Card>
            </div>
          </TabsContent>
          
          <TabsContent value="topics" className="pt-6">
            <div className="space-y-6">
              {agentResults.trends && agentResults.trends.map((trend, index) => (
                <Card key={index} className="overflow-hidden">
                  <CardHeader className="pb-2">
                    <div className="flex justify-between">
                      <CardTitle className="flex items-center gap-2 text-base">
                        <TrendingUp className="h-5 w-5 text-primary" />
                        {trend.topic}
                        <Badge className={getRiskColorClass(trend.misinformation_risk?.level || 'medium')}>
                          {trend.misinformation_risk?.level || 'medium'} risk
                        </Badge>
                      </CardTitle>
                      {trend.sentiment && (
                        <Badge variant="outline" className="gap-1">
                          {getSentimentIcon(trend.sentiment)}
                          <span className="capitalize">{trend.sentiment}</span>
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <h4 className="text-sm font-medium mb-2">Risk Assessment</h4>
                        <div className="space-y-2">
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span>Misinformation Risk</span>
                              <span className="font-medium">{Math.round(trend.misinformation_score * 100)}%</span>
                            </div>
                            <Progress value={trend.misinformation_score * 100} 
                              className={
                                trend.misinformation_risk?.level === 'high' ? 'bg-danger/20' :
                                trend.misinformation_risk?.level === 'medium' ? 'bg-warning/20' : 'bg-success/20'
                              }
                            />
                          </div>
                          
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span>Credibility Score</span>
                              <span className="font-medium">{Math.round(trend.metrics.credibility_score * 100)}%</span>
                            </div>
                            <Progress value={trend.metrics.credibility_score * 100} className="bg-primary/20" />
                          </div>
                          
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span>Analysis Confidence</span>
                              <span className="font-medium">{Math.round(trend.metrics.confidence * 100)}%</span>
                            </div>
                            <Progress value={trend.metrics.confidence * 100} className="bg-muted" />
                          </div>
                        </div>
                        
                        {trend.article_count > 0 && (
                          <p className="text-xs text-muted-foreground mt-3">
                            Based on analysis of {trend.article_count} articles
                          </p>
                        )}
                      </div>
                      
                      <div>
                        <h4 className="text-sm font-medium mb-2">Analysis Justification</h4>
                        <p className="text-sm text-muted-foreground">{trend.justification || "No justification available"}</p>
                        
                        <div className="flex gap-2 mt-4">
                          <div className="flex flex-col items-center justify-center gap-1 bg-muted/30 rounded-md p-2 flex-1">
                            <Gauge className="h-4 w-4 text-muted-foreground" />
                            <span className="text-xs font-medium">Emotional Language</span>
                            <span className="text-sm font-bold">
                              {Math.round(trend.metrics.emotional_language * 100)}%
                            </span>
                          </div>
                          
                          <div className="flex flex-col items-center justify-center gap-1 bg-muted/30 rounded-md p-2 flex-1">
                            <UserCheck className="h-4 w-4 text-muted-foreground" />
                            <span className="text-xs font-medium">Source Reliability</span>
                            <span className="text-sm font-bold">
                              {Math.round(trend.metrics.source_reliability * 100)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {trend.article_analyses && trend.article_analyses.length > 0 && (
                      <Collapsible className="mt-4">
                        <CollapsibleTrigger className="flex items-center gap-1 text-sm font-medium text-primary">
                          <Link2 className="h-4 w-4" />
                          Show Source Analysis
                        </CollapsibleTrigger>
                        <CollapsibleContent className="mt-2 space-y-2">
                          {trend.article_analyses.map((article, idx) => (
                            <div key={idx} className="text-sm bg-muted/30 p-3 rounded-md">
                              <div className="flex items-center justify-between">
                                <Badge variant="outline" className="font-normal">
                                  {article.article_source || 'Unknown Source'}
                                </Badge>
                                {article.misinformation_risk && (
                                  <Badge className={getRiskColorClass(article.misinformation_risk.level)}>
                                    {article.misinformation_risk.level}
                                  </Badge>
                                )}
                              </div>
                              <p className="font-medium mt-2">{article.article_title}</p>
                              <p className="text-muted-foreground mt-1 text-xs">{article.text_snippet}</p>
                            </div>
                          ))}
                        </CollapsibleContent>
                      </Collapsible>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
          
          <TabsContent value="indicators" className="pt-6">
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-danger" />
                    Top Misinformation Indicators
                  </CardTitle>
                  <CardDescription>Most common signals of potential misinformation</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {metrics.top_misinformation_indicators?.map((indicator, i) => (
                      <div key={i} className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <X className="h-4 w-4 text-danger" />
                          <span className="text-sm">{indicator.name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{indicator.count}</Badge>
                          <Progress value={(indicator.count / metrics.topics_analyzed) * 100} className="w-20 bg-danger/20" />
                        </div>
                      </div>
                    ))}
                    
                    {(!metrics.top_misinformation_indicators || metrics.top_misinformation_indicators.length === 0) && (
                      <p className="text-muted-foreground text-sm">No indicators detected</p>
                    )}
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Check className="h-4 w-4 text-verified" />
                    Top Credibility Indicators
                  </CardTitle>
                  <CardDescription>Most common signals of credible information</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {metrics.top_credibility_indicators?.map((indicator, i) => (
                      <div key={i} className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-verified" />
                          <span className="text-sm">{indicator.name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{indicator.count}</Badge>
                          <Progress value={(indicator.count / metrics.topics_analyzed) * 100} className="w-20 bg-verified/20" />
                        </div>
                      </div>
                    ))}
                    
                    {(!metrics.top_credibility_indicators || metrics.top_credibility_indicators.length === 0) && (
                      <p className="text-muted-foreground text-sm">No indicators detected</p>
                    )}
                  </div>
                </CardContent>
              </Card>
              
              {agentResults.using_gemini && (
                <Card className="md:col-span-2">
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Brain className="h-4 w-4 text-primary" />
                      Gemini API Enhanced Analysis
                    </CardTitle>
                    <CardDescription>Advanced AI analysis of misinformation patterns</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {agentResults.trends?.filter(t => t.gemini_analysis).map((trend, i) => (
                      <div key={i} className="mb-4 last:mb-0">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline">{trend.topic}</Badge>
                          <Separator className="flex-1" />
                        </div>
                        <p className="text-sm">{trend.gemini_analysis}</p>
                      </div>
                    ))}
                    
                    {!agentResults.trends?.some(t => t.gemini_analysis) && (
                      <div className="bg-primary/5 p-4 rounded-md">
                        <p className="text-sm">Gemini API is enabled but no enhanced analysis is available for the current trends.</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    );
  };

  const renderAgentAnalysis = () => {
    // If agent status shows it's not available, show a special message
    if (agentStatus && agentStatus.available === false) {
      return (
        <Card className="bg-muted/30">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Brain className="h-5 w-5 mr-2 text-muted-foreground" />
              AI Analysis Unavailable
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground mb-4">
              The AI analysis service is currently unavailable. This could be due to missing dependencies on the server.
            </p>
            <div className="bg-primary/5 p-4 rounded-md border border-primary/20">
              <h4 className="font-medium mb-2">Server Message:</h4>
            </div>
          </CardContent>
        </Card>
      );
    }

    if (agentError) {
      return (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="p-4 bg-danger/10 text-danger rounded-md"
        >
          {agentError}
        </motion.div>
      );
    }
    
    if (!agentResults) {
      return (
        <div className="text-center py-8">
          <p className="text-muted-foreground">No agent analysis available</p>
          <Button 
            variant="default" 
            onClick={triggerAgentAnalysis} 
            disabled={isAgentRefreshing || (agentStatus && agentStatus.running)}
            className="mt-4"
          >
            {isAgentRefreshing ? (
              <><RefreshCw className="h-4 w-4 mr-2 animate-spin" /> Analyzing...</>
            ) : (
              <><Brain className="h-4 w-4 mr-2" /> Run AI Analysis</>
            )}
          </Button>
        </div>
      );
    }
    
    // Render the agent analysis results
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-sm text-muted-foreground">
              Last analyzed: {new Date(agentResults.timestamp).toLocaleString()}
            </p>
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={triggerAgentAnalysis} 
            disabled={isAgentRefreshing || (agentStatus && agentStatus.running)}
          >
            {isAgentRefreshing ? (
              <><RefreshCw className="h-4 w-4 mr-2 animate-spin" /> Analyzing...</>
            ) : (
              <><RefreshCw className="h-4 w-4 mr-2" /> Refresh Analysis</>
            )}
          </Button>
        </div>
        
        {agentResults.error ? (
          <Card className="bg-danger/5 border-danger/20">
            <CardHeader>
              <CardTitle className="text-danger flex items-center">
                <AlertTriangle className="h-5 w-5 mr-2" />
                Analysis Error
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p>{agentResults.error}</p>
            </CardContent>
          </Card>
        ) : (
          <>
            {renderAgentDashboard()}
          </>
        )}
      </div>
    );
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
            className="inline-flex items-center gap-2 px-4 py-2 bg-warning/10 rounded-full"
          >
            <Activity className="h-5 w-5 text-warning" />
            <span className="text-warning font-medium">Live Monitoring</span>
          </motion.div>
          
          <motion.h1 
            className="text-4xl md:text-6xl font-bold text-gradient"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            Social Media Trends
          </motion.h1>
          
          <motion.p 
            className="text-xl text-muted-foreground max-w-2xl mx-auto"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            Real-time monitoring of misinformation trends across social media platforms
          </motion.p>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="trends" value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full max-w-md mx-auto grid-cols-2">
            <TabsTrigger value="trends">
              <TrendingUp className="h-4 w-4 mr-2" />
              Trends
            </TabsTrigger>
            <TabsTrigger value="analysis">
              <Brain className="h-4 w-4 mr-2" />
              AI Analysis
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="trends" className="mt-6">
            {/* Controls */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="flex flex-wrap justify-between items-center gap-4 mb-6"
            >
              <div className="flex gap-2">
                {['all', 'twitter', 'facebook', 'instagram', 'tiktok'].map((platform) => (
                  <Button
                    key={platform}
                    variant={selectedPlatform === platform ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedPlatform(platform)}
                    className="capitalize"
                  >
                    {platform}
                  </Button>
                ))}
              </div>
              
              <Button
                onClick={handleRefresh}
                disabled={isRefreshing}
                variant="outline"
                size="sm"
              >
                <motion.div
                  animate={{ rotate: isRefreshing ? 360 : 0 }}
                  transition={{ duration: 1, repeat: isRefreshing ? Infinity : 0 }}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                </motion.div>
                Refresh
              </Button>
            </motion.div>

            {/* Error message */}
            {error && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="p-4 bg-danger/10 text-danger rounded-md mb-6"
              >
                {error}
              </motion.div>
            )}

            {/* Trends Grid */}
            <div className="grid gap-6">
              <AnimatePresence mode="wait">
                {filteredTrends.map((trend, index) => (
                  <motion.div
                    key={trend.id}
                    initial={{ opacity: 0, y: 50 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -50 }}
                    transition={{ delay: index * 0.1 }}
                    whileHover={{ scale: 1.02 }}
                  >
                    <Card className="glass-card hover:shadow-lg transition-shadow">
                      <CardHeader className="pb-4">
                        <div className="flex items-start justify-between">
                          <div className="space-y-2">
                            <CardTitle className="flex items-center gap-3">
                              <TrendingUp className="h-5 w-5 text-primary" />
                              {trend.topic}
                              <Badge className={getRiskColorClass(trend.misinformationRisk)}>
                                {trend.misinformationRisk} risk
                              </Badge>
                            </CardTitle>
                            <div className="flex items-center gap-4 text-sm text-muted-foreground">
                              <div className="flex items-center gap-1">
                                {getPlatformIcon(trend.platform)}
                                <span className="capitalize">{trend.platform}</span>
                              </div>
                              <span>{trend.mentions.toLocaleString()} mentions</span>
                              <span>{trend.timestamp}</span>
                            </div>
                          </div>
                          
                          {trend.misinformationRisk === 'high' && (
                            <motion.div
                              animate={{ scale: [1, 1.1, 1] }}
                              transition={{ duration: 2, repeat: Infinity }}
                            >
                              <AlertTriangle className="h-6 w-6 text-danger" />
                            </motion.div>
                          )}
                        </div>
                      </CardHeader>
                      
                      <CardContent>
                        <p className="text-muted-foreground mb-4">{trend.description}</p>
                        
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium">Activity Level:</span>
                            <div className="flex items-center gap-1">
                              {[...Array(5)].map((_, i) => (
                                <motion.div
                                  key={i}
                                  className={`h-2 w-2 rounded-full ${
                                    i < (trend.mentions / 10000) ? 'bg-primary' : 'bg-muted'
                                  }`}
                                  initial={{ scale: 0 }}
                                  animate={{ scale: 1 }}
                                  transition={{ delay: i * 0.1 }}
                                />
                              ))}
                            </div>
                          </div>
                          
                          <Button variant="outline" size="sm">
                            View Details
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </TabsContent>
          
          <TabsContent value="analysis" className="mt-6">
            {renderAgentAnalysis()}
          </TabsContent>
        </Tabs>
      </motion.div>
    </PageLayout>
  );
}
