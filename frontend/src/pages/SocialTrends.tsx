import { useState, useEffect } from 'react';
import axios from 'axios';
import { PageLayout } from '@/components/layout/PageLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TrendingUp, AlertTriangle, Twitter, Globe, RefreshCw, Activity, Brain, BarChart2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useInView } from 'react-intersection-observer';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';

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
}

interface AgentAnalysis {
  success: boolean;
  timestamp: string;
  analysis?: string;
  trends?: any[];
  error?: string;
}

export default function SocialTrends() {
  const [trends, setTrends] = useState<TrendItem[]>(mockTrends);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('trends');
  
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
      const response = await axios.get('http://localhost:8000/api/trends');
      
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
      const response = await axios.get('http://localhost:8000/api/agent/status');
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
      const response = await axios.get('http://localhost:8000/api/agent/results');
      setAgentResults(response.data);
      setAgentError(null);
    } catch (error: any) {
      console.error('Error fetching agent results:', error);
      setAgentError('Could not load agent analysis results');
    }
  };

  const triggerAgentAnalysis = async () => {
    setIsAgentRefreshing(true);
    setAgentError(null);
    
    try {
      await axios.post('http://localhost:8000/api/agent/analyze');
      
      // Poll for status
      const checkStatus = async () => {
        const status = await axios.get('http://localhost:8000/api/agent/status');
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
      default: return <Globe className="h-4 w-4" />;
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'high': return 'text-danger bg-danger/10';
      case 'medium': return 'text-warning bg-warning/10';
      case 'low': return 'text-verified bg-verified/10';
      default: return 'text-muted-foreground bg-muted/10';
    }
  };

  const filteredTrends = selectedPlatform === 'all' 
    ? trends 
    : trends.filter(trend => trend.platform === selectedPlatform);

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
              <p className="text-sm">
                {agentResults?.message || agentResults?.analysis || "No message available from the server."}
              </p>
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
            {agentResults.analysis && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Brain className="h-5 w-5 mr-2 text-primary" />
                    AI Analysis Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="whitespace-pre-line">{agentResults.analysis}</p>
                </CardContent>
              </Card>
            )}
            
            {agentResults.trends && agentResults.trends.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Analyzed Trends</h3>
                
                {agentResults.trends.map((trend, index) => (
                  <Card key={index} className="overflow-hidden">
                    <CardHeader className="pb-2">
                      <CardTitle className="flex items-center gap-2 text-base">
                        <TrendingUp className="h-5 w-5 text-primary" />
                        {trend.topic}
                        {trend.misinformation_risk && (
                          <Badge className={getRiskColor(trend.misinformation_risk.level)}>
                            {trend.misinformation_risk.level} risk
                          </Badge>
                        )}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="pb-4">
                      {trend.misinformation_risk && trend.misinformation_risk.score !== undefined && (
                        <div className="mb-4">
                          <div className="flex justify-between text-sm mb-1">
                            <span>Misinformation Risk Score</span>
                            <span className="font-medium">{Math.round(trend.misinformation_risk.score * 100)}%</span>
                          </div>
                          <Progress value={trend.misinformation_risk.score * 100} 
                            className={
                              trend.misinformation_risk.level === 'high' ? 'bg-danger/20' :
                              trend.misinformation_risk.level === 'medium' ? 'bg-warning/20' : 'bg-success/20'
                            }
                          />
                        </div>
                      )}
                      
                      {trend.articles_analyzed > 0 && (
                        <p className="text-sm text-muted-foreground mb-2">
                          Based on analysis of {trend.articles_analyzed} articles
                        </p>
                      )}
                      
                      {trend.article_analyses && trend.article_analyses.length > 0 && (
                        <div className="mt-3 space-y-3">
                          <h4 className="text-sm font-medium">Key Sources:</h4>
                          {trend.article_analyses.slice(0, 2).map((article, idx) => (
                            <div key={idx} className="text-sm bg-muted/30 p-3 rounded-md">
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="font-normal">
                                  {article.article_source || 'Unknown Source'}
                                </Badge>
                                {article.misinformation_risk && (
                                  <Badge className={getRiskColor(article.misinformation_risk.level)}>
                                    {article.misinformation_risk.level}
                                  </Badge>
                                )}
                              </div>
                              <p className="font-medium mt-1">{article.article_title}</p>
                              <p className="text-muted-foreground mt-1 text-xs">{article.text_snippet}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
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
                          <Badge className={getRiskColor(trend.misinformationRisk)}>
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
