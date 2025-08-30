import { useState, useEffect } from 'react';
import axios from 'axios';
import { PageLayout } from '@/components/layout/PageLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TrendingUp, AlertTriangle, Twitter, Globe, RefreshCw, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useInView } from 'react-intersection-observer';

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

export default function SocialTrends() {
  const [trends, setTrends] = useState<TrendItem[]>(mockTrends);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);
  
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

  // Initial data fetch
  useEffect(() => {
    fetchTrends();
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

        {/* Controls */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="flex flex-wrap justify-between items-center gap-4"
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
            className="p-4 bg-danger/10 text-danger rounded-md"
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
      </motion.div>
    </PageLayout>
  );
}
