
import { useState, useEffect } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Info, ExternalLink, User, Calendar, Globe, Zap } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';

interface AnalysisResult {
  overall_credibility: number;
  claim_verification: {
    status: 'verified' | 'false' | 'questionable' | 'unverified';
    confidence: number;
    summary: string;
  };
  source_analysis: {
    domain_credibility: number;
    author_credibility: number;
    publication_date: string;
    bias_score: number;
  };
  fact_checks: Array<{
    source: string;
    url: string;
    verdict: string;
    date: string;
  }>;
  ai_analysis: {
    deepfake_detection?: number;
    sentiment_bias: number;
    language_patterns: string[];
  };
  evidence: Array<{
    type: 'supporting' | 'contradicting';
    source: string;
    excerpt: string;
    credibility: number;
  }>;
}

interface AnalysisResultsProps {
  data: any;
  isLoading: boolean;
}

export const AnalysisResults = ({ data, isLoading }: AnalysisResultsProps) => {
  const [progress, setProgress] = useState(0);
  const [showResults, setShowResults] = useState(false);

  // Simulated analysis results
  const mockResult: AnalysisResult = {
    overall_credibility: 75,
    claim_verification: {
      status: 'questionable',
      confidence: 68,
      summary: 'The claim contains some factual elements but lacks context and may be misleading. Key details require verification from authoritative sources.'
    },
    source_analysis: {
      domain_credibility: 82,
      author_credibility: 71,
      publication_date: '2024-01-15',
      bias_score: 25
    },
    fact_checks: [
      {
        source: 'Snopes',
        url: 'https://snopes.com/example',
        verdict: 'Mixture',
        date: '2024-01-10'
      },
      {
        source: 'PolitiFact',
        url: 'https://politifact.com/example',
        verdict: 'Half True',
        date: '2024-01-12'
      }
    ],
    ai_analysis: {
      deepfake_detection: 15,
      sentiment_bias: 32,
      language_patterns: ['Emotional language', 'Selective statistics', 'Missing context']
    },
    evidence: [
      {
        type: 'supporting',
        source: 'Reuters',
        excerpt: 'Official data confirms the general trend mentioned in the claim...',
        credibility: 95
      },
      {
        type: 'contradicting',
        source: 'Associated Press',
        excerpt: 'However, the specific numbers cited appear to be outdated...',
        credibility: 92
      }
    ]
  };

  useEffect(() => {
    if (isLoading) {
      setShowResults(false);
      setProgress(0);
      // Simulate progressive analysis
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 100) {
            clearInterval(interval);
            setTimeout(() => setShowResults(true), 500);
            return 100;
          }
          return prev + Math.random() * 15;
        });
      }, 200);

      return () => clearInterval(interval);
    }
  }, [isLoading]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'verified': return 'verified';
      case 'false': return 'false';
      case 'questionable': return 'questionable';
      default: return 'neutral';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'verified': return <CheckCircle className="h-5 w-5" />;
      case 'false': return <XCircle className="h-5 w-5" />;
      case 'questionable': return <AlertTriangle className="h-5 w-5" />;
      default: return <Info className="h-5 w-5" />;
    }
  };

  if (!data && !isLoading) return null;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Progress Indicator */}
      {isLoading && !showResults && (
        <Card className="p-6">
          <div className="space-y-4 text-center">
            <div className="relative inline-flex">
              <Zap className="h-8 w-8 text-primary animate-pulse" />
              <div className="absolute inset-0 pulse-ring" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">Analyzing Content</h3>
              <p className="text-sm text-muted-foreground">
                Running multi-modal verification checks...
              </p>
            </div>
            <div className="space-y-2">
              <Progress value={progress} className="h-2" />
              <div className="text-xs text-muted-foreground">
                {progress < 30 && "Processing content..."}
                {progress >= 30 && progress < 60 && "Checking fact databases..."}
                {progress >= 60 && progress < 90 && "Analyzing sources..."}
                {progress >= 90 && "Finalizing results..."}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Main Results */}
      {showResults && data && (
        <div className="space-y-6 slide-up">
          {/* Overall Assessment */}
          <Card className="border-2 border-primary/20">
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-3">
                  <div className={`p-2 rounded-full bg-${getStatusColor(mockResult.claim_verification.status)}/10`}>
                    {getStatusIcon(mockResult.claim_verification.status)}
                  </div>
                  Verification Results
                </CardTitle>
                <Badge 
                  variant="outline" 
                  className={`bg-${getStatusColor(mockResult.claim_verification.status)}/10 border-${getStatusColor(mockResult.claim_verification.status)}/20`}
                >
                  {mockResult.claim_verification.confidence}% Confidence
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Overall Credibility</span>
                  <span className="font-medium">{mockResult.overall_credibility}%</span>
                </div>
                <div 
                  className={`credibility-meter credibility-${getStatusColor(mockResult.claim_verification.status)}`}
                  style={{ '--score': `${mockResult.overall_credibility}%` } as any}
                />
              </div>
              <p className="text-muted-foreground leading-relaxed">
                {mockResult.claim_verification.summary}
              </p>
            </CardContent>
          </Card>

          {/* Source Analysis */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                Source Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <div className="text-2xl font-bold text-primary">
                    {mockResult.source_analysis.domain_credibility}%
                  </div>
                  <div className="text-sm text-muted-foreground">Domain Trust</div>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <div className="text-2xl font-bold text-secondary">
                    {mockResult.source_analysis.author_credibility}%
                  </div>
                  <div className="text-sm text-muted-foreground">Author Rating</div>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <div className="text-2xl font-bold text-warning">
                    {mockResult.source_analysis.bias_score}%
                  </div>
                  <div className="text-sm text-muted-foreground">Bias Score</div>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <div className="text-sm font-mono">
                    {new Date(mockResult.source_analysis.publication_date).toLocaleDateString()}
                  </div>
                  <div className="text-sm text-muted-foreground">Published</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Fact Check Cross-References */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5" />
                Fact-Check Cross-References
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockResult.fact_checks.map((check, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="font-medium">{check.source}</div>
                      <Badge variant="outline">{check.verdict}</Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-muted-foreground">{check.date}</span>
                      <Button size="sm" variant="ghost">
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* AI Analysis */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                AI Analysis
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {mockResult.ai_analysis.deepfake_detection && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Deepfake Detection</span>
                    <span className="font-medium">{mockResult.ai_analysis.deepfake_detection}% risk</span>
                  </div>
                  <Progress value={mockResult.ai_analysis.deepfake_detection} className="h-1" />
                </div>
              )}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Sentiment Bias</span>
                  <span className="font-medium">{mockResult.ai_analysis.sentiment_bias}%</span>
                </div>
                <Progress value={mockResult.ai_analysis.sentiment_bias} className="h-1" />
              </div>
              <div className="space-y-2">
                <div className="text-sm font-medium">Language Patterns Detected:</div>
                <div className="flex flex-wrap gap-2">
                  {mockResult.ai_analysis.language_patterns.map((pattern, index) => (
                    <Badge key={index} variant="secondary">{pattern}</Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Evidence Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Supporting Evidence</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockResult.evidence.map((item, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full bg-${item.type === 'supporting' ? 'verified' : 'warning'}`} />
                        <span className="font-medium">{item.source}</span>
                        <Badge variant="outline" className="text-xs">
                          {item.credibility}% credible
                        </Badge>
                      </div>
                      <Badge variant={item.type === 'supporting' ? 'default' : 'secondary'}>
                        {item.type}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground pl-4 border-l-2 border-muted">
                      {item.excerpt}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
