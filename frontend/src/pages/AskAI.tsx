import { useState, useRef, useEffect } from 'react';
import { PageLayout } from '@/components/layout/PageLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  MessageSquare, 
  Send, 
  Bot, 
  User, 
  Loader2, 
  ExternalLink, 
  Brain, 
  Sparkles, 
  Search, 
  BookOpen, 
  Shield,
  Zap,
  Star,
  Globe,
  Database,
  CheckCircle,
  Clock,
  TrendingUp,
  Award,
  Lightbulb,
  Target,
  Filter
} from 'lucide-react';
import { motion, AnimatePresence, useScroll, useTransform } from 'framer-motion';
import { useInView } from 'react-intersection-observer';

// ... keep existing code (interfaces and components like TypingEffect, FloatingCard, StatCard)

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  sources?: Array<{
    title: string;
    url: string;
    snippet: string;
    credibility: number;
    domain: string;
    publishDate: string;
  }>;
  confidence?: number;
  processingTime?: number;
}

const TypingEffect = ({ text, speed = 30 }: { text: string; speed?: number }) => {
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timeout = setTimeout(() => {
        setDisplayText(prev => prev + text[currentIndex]);
        setCurrentIndex(prev => prev + 1);
      }, speed);
      return () => clearTimeout(timeout);
    }
  }, [currentIndex, text, speed]);

  return <span>{displayText}</span>;
};

const FloatingCard = ({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay, duration: 0.6, type: "spring", stiffness: 100 }}
    whileHover={{ y: -5, scale: 1.02 }}
    className="glass-card p-4 sm:p-6 floating-animation"
  >
    {children}
  </motion.div>
);

const StatCard = ({ icon: Icon, value, label, gradient }: { 
  icon: any; 
  value: string; 
  label: string; 
  gradient: string;
}) => (
  <motion.div
    whileHover={{ scale: 1.05 }}
    className="relative overflow-hidden rounded-lg p-3 sm:p-4 bg-gradient-to-br from-background/50 to-muted/20 border border-border/50"
  >
    <div className={`absolute inset-0 ${gradient} opacity-5`} />
    <div className="relative flex items-center gap-2 sm:gap-3">
      <div className={`p-1.5 sm:p-2 rounded-lg ${gradient} bg-opacity-10`}>
        <Icon className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
      </div>
      <div>
        <div className="text-lg sm:text-2xl font-bold text-foreground">{value}</div>
        <div className="text-xs sm:text-sm text-muted-foreground">{label}</div>
      </div>
    </div>
  </motion.div>
);

export default function AskAI() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { scrollY } = useScroll();
  const y1 = useTransform(scrollY, [0, 300], [0, -50]);
  const y2 = useTransform(scrollY, [0, 300], [0, -25]);
  
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    // Only scroll to bottom if there are messages and not showing welcome screen
    if (messages.length > 0 && !showWelcome) {
      scrollToBottom();
    }
  }, [messages, showWelcome]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setShowWelcome(false);

    // Simulate AI response with realistic processing time
    const processingDelay = 2000 + Math.random() * 3000;
    
    setTimeout(() => {
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: `Based on your inquiry about "${inputValue}", I've conducted a comprehensive analysis across multiple reliable sources. Here's what I found:

**Key Findings:**
• Primary information has been verified through cross-referencing with academic databases and fact-checking organizations
• Analysis includes recent developments and historical context to provide complete understanding
• Multiple perspectives have been considered to ensure balanced reporting
• Statistical data has been validated through official government and research institution sources

**Detailed Analysis:**
The research indicates consistent patterns across reputable sources, with high confidence in the accuracy of the information presented. This analysis incorporates both quantitative data and qualitative insights from domain experts.

**Confidence Assessment:**
Based on source reliability, consistency of reporting, and evidence quality, this information carries a high confidence rating with strong evidentiary support.`,
        timestamp: new Date(),
        confidence: 92 + Math.floor(Math.random() * 7),
        processingTime: processingDelay / 1000,
        sources: [
          {
            title: 'Reuters Fact Check Database',
            url: 'https://reuters.com/fact-check',
            snippet: 'Comprehensive fact-checking with rigorous verification standards and transparent methodology...',
            credibility: 96,
            domain: 'reuters.com',
            publishDate: '2024-01-15'
          },
          {
            title: 'Associated Press News',
            url: 'https://apnews.com',
            snippet: 'Breaking news coverage with strict editorial standards and global correspondent network...',
            credibility: 94,
            domain: 'apnews.com',
            publishDate: '2024-01-14'
          },
          {
            title: 'Academic Research Portal - Nature',
            url: 'https://nature.com',
            snippet: 'Peer-reviewed scientific publications with rigorous review process and citation tracking...',
            credibility: 98,
            domain: 'nature.com',
            publishDate: '2024-01-10'
          },
          {
            title: 'Government Statistical Office',
            url: 'https://data.gov',
            snippet: 'Official government statistics with transparent data collection and regular updates...',
            credibility: 95,
            domain: 'data.gov',
            publishDate: '2024-01-12'
          },
          {
            title: 'World Health Organization',
            url: 'https://who.int',
            snippet: 'Global health authority providing evidence-based guidelines and policy recommendations...',
            credibility: 97,
            domain: 'who.int',
            publishDate: '2024-01-13'
          }
        ]
      };
      
      setMessages(prev => [...prev, botMessage]);
      setIsLoading(false);
    }, processingDelay);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const suggestedQuestions = [
    "What are the latest developments in renewable energy technology?",
    "How does artificial intelligence impact modern healthcare?",
    "What are the economic implications of climate change?",
    "Explain quantum computing and its potential applications",
    "What are the current trends in sustainable agriculture?"
  ];

  return (
    <PageLayout className="py-4 sm:py-8">
      <motion.div
        ref={ref}
        initial={{ opacity: 0, y: 50 }}
        animate={inView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.8 }}
        className="space-y-8 sm:space-y-12"
      >
        {/* Enhanced Hero Section */}
        <div className="text-center space-y-6 sm:space-y-8 relative">
          <motion.div
            style={{ y: y1 }}
            className="absolute -top-10 sm:-top-20 left-1/2 transform -translate-x-1/2 opacity-10"
          >
            {/* <Brain className="h-16 w-16 sm:h-32 sm:w-32 text-primary" /> */}
          </motion.div>
          
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            className="inline-flex items-center gap-2 sm:gap-3 px-4 sm:px-6 py-2 sm:py-3 bg-gradient-to-r from-primary/10 to-secondary/10 rounded-full border border-primary/20"
          >
            <Sparkles className="h-5 w-5 sm:h-6 sm:w-6 text-primary animate-pulse" />
            <span className="text-primary font-semibold text-sm sm:text-lg">AI-Powered Knowledge Engine</span>
            <Sparkles className="h-5 w-5 sm:h-6 sm:w-6 text-secondary animate-pulse" />
          </motion.div>
          
          <motion.h1 
            className="text-4xl sm:text-5xl md:text-7xl font-bold text-gradient-colorful leading-tight"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.8 }}
          >
            <TypingEffect text="Ask AI" speed={100} />
          </motion.h1>
          
          <motion.p 
            className="text-lg sm:text-xl md:text-2xl text-muted-foreground max-w-4xl mx-auto leading-relaxed px-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.6 }}
          >
            Unlock comprehensive, fact-checked insights on any topic with our advanced AI research assistant. 
            Get verified information with credible sources, real-time analysis, and expert-level understanding.
          </motion.p>

          {/* Feature Stats */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 max-w-4xl mx-auto mt-8 sm:mt-12 px-4"
          >
            <StatCard 
              icon={Database} 
              value="50M+" 
              label="Sources Indexed" 
              gradient="gradient-primary"
            />
            <StatCard 
              icon={Shield} 
              value="99.2%" 
              label="Accuracy Rate" 
              gradient="gradient-primary"
            />
            <StatCard 
              icon={Zap} 
              value="< 3s" 
              label="Response Time" 
              gradient="gradient-primary"
            />
            <StatCard 
              icon={Globe} 
              value="190+" 
              label="Languages" 
              gradient="gradient-primary"
            />
          </motion.div>
        </div>

        {/* Enhanced Features Section */}
        <motion.div
          style={{ y: y2 }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8 max-w-6xl mx-auto px-4"
        >
          <FloatingCard delay={0.9}>
            <div className="text-center space-y-4">
              <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center">
                <Search className="h-6 w-6 sm:h-8 sm:w-8 text-white" />
              </div>
              <h3 className="text-lg sm:text-xl font-bold">Deep Research</h3>
              <p className="text-sm sm:text-base text-muted-foreground">Advanced algorithms search through millions of verified sources to provide comprehensive answers</p>
            </div>
          </FloatingCard>

          <FloatingCard delay={1.0}>
            <div className="text-center space-y-4">
              <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto bg-gradient-to-br from-secondary to-warning rounded-full flex items-center justify-center">
                <Shield className="h-6 w-6 sm:h-8 sm:w-8 text-white" />
              </div>
              <h3 className="text-lg sm:text-xl font-bold">Fact Verification</h3>
              <p className="text-sm sm:text-base text-muted-foreground">Every piece of information is cross-referenced and verified against authoritative sources</p>
            </div>
          </FloatingCard>

          <FloatingCard delay={1.1}>
            <div className="text-center space-y-4">
              <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto bg-gradient-to-br from-warning to-danger rounded-full flex items-center justify-center">
                <Lightbulb className="h-6 w-6 sm:h-8 sm:w-8 text-white" />
              </div>
              <h3 className="text-lg sm:text-xl font-bold">Smart Insights</h3>
              <p className="text-sm sm:text-base text-muted-foreground">AI-powered analysis provides context, implications, and connections you might have missed</p>
            </div>
          </FloatingCard>
        </motion.div>

        {/* Enhanced Chat Interface */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2 }}
          className="max-w-6xl mx-auto px-4"
        >
          <Card className="glass-card flex flex-col overflow-hidden border-2 border-primary/20 h-[80vh] sm:h-[700px]">
            <CardHeader className="border-b border-border/50 bg-gradient-to-r from-primary/5 to-secondary/5 p-4 sm:p-6">
              <CardTitle className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <MessageSquare className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
                    <div className="absolute -top-1 -right-1 w-2 h-2 sm:w-3 sm:h-3 bg-green-500 rounded-full animate-pulse" />
                  </div>
                  <span className="text-lg sm:text-xl">AI Research Assistant</span>
                  <Badge variant="outline" className="text-green-600 border-green-600">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse" />
                    Online
                  </Badge>
                </div>
                <div className="flex items-center gap-2 text-xs sm:text-sm text-muted-foreground">
                  <Clock className="h-3 w-3 sm:h-4 sm:w-4" />
                  Real-time Analysis
                </div>
              </CardTitle>
            </CardHeader>
            
            <CardContent className="flex-1 flex flex-col p-0 min-h-0">
              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 sm:space-y-6">
                {/* Welcome Message */}
                <AnimatePresence>
                  {showWelcome && messages.length === 0 && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      className="text-center space-y-6 sm:space-y-8 py-8 sm:py-12"
                    >
                      <div className="w-16 h-16 sm:w-20 sm:h-20 mx-auto bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center">
                        <Bot className="h-8 w-8 sm:h-10 sm:w-10 text-white" />
                      </div>
                      <div className="space-y-4">
                        <h3 className="text-xl sm:text-2xl font-bold text-gradient">
                          Welcome to Advanced AI Research
                        </h3>
                        <p className="text-sm sm:text-base text-muted-foreground max-w-2xl mx-auto px-4">
                          Ask me anything and I'll provide comprehensive, fact-checked information with credible sources. 
                          From current events to complex topics, I'm here to help you understand the world better.
                        </p>
                      </div>

                      {/* Suggested Questions */}
                      <div className="space-y-4">
                        <h4 className="text-base sm:text-lg font-semibold flex items-center justify-center gap-2">
                          <Target className="h-4 w-4 sm:h-5 sm:w-5 text-primary" />
                          Popular Questions
                        </h4>
                        <div className="grid grid-cols-1 gap-3 max-w-4xl mx-auto">
                          {suggestedQuestions.map((question, index) => (
                            <motion.button
                              key={index}
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: 0.1 * index }}
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                              onClick={() => setInputValue(question)}
                              className="p-3 text-left bg-muted/50 hover:bg-muted rounded-lg border border-border/50 hover:border-primary/50 transition-all duration-200"
                            >
                              <p className="text-xs sm:text-sm font-medium">{question}</p>
                            </motion.button>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Messages */}
                <AnimatePresence>
                  {messages.map((message) => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      className={`flex gap-3 sm:gap-4 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      {message.type === 'bot' && (
                        <div className="flex-shrink-0">
                          <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                            <Bot className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
                          </div>
                        </div>
                      )}
                      
                      <div className={`max-w-[90%] sm:max-w-[85%] ${message.type === 'user' ? 'order-2' : ''}`}>
                        <div className={`p-3 sm:p-4 rounded-2xl ${
                          message.type === 'user' 
                            ? 'bg-gradient-to-r from-primary to-secondary text-white ml-auto' 
                            : 'bg-muted/70 border border-border/50'
                        }`}>
                          <div className="whitespace-pre-wrap text-sm sm:text-base">{message.content}</div>
                          
                          {/* Confidence and Processing Time */}
                          {message.type === 'bot' && message.confidence && (
                            <div className="mt-4 flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4 text-xs sm:text-sm text-muted-foreground">
                              <div className="flex items-center gap-2">
                                <Award className="h-3 w-3 sm:h-4 sm:w-4" />
                                <span>Confidence: {message.confidence}%</span>
                                <Progress value={message.confidence} className="w-12 sm:w-16 h-2" />
                              </div>
                              {message.processingTime && (
                                <div className="flex items-center gap-1">
                                  <Clock className="h-3 w-3 sm:h-4 sm:w-4" />
                                  <span>{message.processingTime.toFixed(1)}s</span>
                                </div>
                              )}
                            </div>
                          )}
                          
                          {/* Enhanced Sources */}
                          {message.sources && (
                            <div className="mt-4 sm:mt-6 space-y-4">
                              <div className="flex items-center gap-2">
                                <BookOpen className="h-3 w-3 sm:h-4 sm:w-4 text-primary" />
                                <h4 className="text-xs sm:text-sm font-semibold">Verified Sources</h4>
                                <Badge variant="outline" className="text-xs">
                                  {message.sources.length} sources
                                </Badge>
                              </div>
                              <div className="grid gap-3">
                                {message.sources.map((source, index) => (
                                  <motion.div
                                    key={index}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.1 }}
                                    className="group p-3 sm:p-4 bg-background/80 border border-border/50 rounded-xl hover:border-primary/50 transition-all duration-200"
                                  >
                                    <div className="flex items-start justify-between gap-3">
                                      <div className="flex-1 space-y-2">
                                        <div className="flex items-center gap-2">
                                          <h5 className="text-xs sm:text-sm font-semibold group-hover:text-primary transition-colors">
                                            {source.title}
                                          </h5>
                                          <ExternalLink className="h-2 w-2 sm:h-3 sm:w-3 opacity-50 group-hover:opacity-100" />
                                        </div>
                                        <p className="text-xs text-muted-foreground leading-relaxed">
                                          {source.snippet}
                                        </p>
                                        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-1 sm:gap-3 text-xs text-muted-foreground">
                                          <span className="flex items-center gap-1">
                                            <Globe className="h-2 w-2 sm:h-3 sm:w-3" />
                                            {source.domain}
                                          </span>
                                          <span className="flex items-center gap-1">
                                            <Clock className="h-2 w-2 sm:h-3 sm:w-3" />
                                            {source.publishDate}
                                          </span>
                                        </div>
                                      </div>
                                      <div className="flex flex-col items-end gap-2">
                                        <Badge 
                                          variant={source.credibility >= 95 ? "default" : source.credibility >= 90 ? "secondary" : "outline"}
                                          className="text-xs whitespace-nowrap"
                                        >
                                          <Star className="h-2 w-2 sm:h-3 sm:w-3 mr-1" />
                                          {source.credibility}% credible
                                        </Badge>
                                        {source.credibility >= 95 && (
                                          <CheckCircle className="h-3 w-3 sm:h-4 sm:w-4 text-green-500" />
                                        )}
                                      </div>
                                    </div>
                                  </motion.div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                        
                        <div className="flex items-center gap-2 mt-2 px-2 text-xs text-muted-foreground">
                          <span>{message.timestamp.toLocaleTimeString()}</span>
                          {message.type === 'bot' && (
                            <>
                              <span>•</span>
                              <TrendingUp className="h-2 w-2 sm:h-3 sm:w-3" />
                              <span>Verified</span>
                            </>
                          )}
                        </div>
                      </div>

                      {message.type === 'user' && (
                        <div className="flex-shrink-0 order-1">
                          <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-secondary to-warning flex items-center justify-center">
                            <User className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
                          </div>
                        </div>
                      )}
                    </motion.div>
                  ))}
                </AnimatePresence>

                {/* Enhanced Loading State */}
                {isLoading && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex gap-3 sm:gap-4"
                  >
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                        <Bot className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
                      </div>
                    </div>
                    <div className="bg-muted/70 border border-border/50 p-3 sm:p-4 rounded-2xl">
                      <div className="flex items-center gap-3 text-muted-foreground">
                        <Loader2 className="h-4 w-4 sm:h-5 sm:w-5 animate-spin" />
                        <div className="space-y-1">
                          <div className="text-xs sm:text-sm font-medium">AI is researching your question...</div>
                          <div className="text-xs flex items-center gap-2">
                            <Filter className="h-2 w-2 sm:h-3 sm:w-3" />
                            Analyzing sources • Cross-referencing facts • Verifying data
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Enhanced Input Area */}
              <div className="border-t border-border/50 p-4 sm:p-6 bg-gradient-to-r from-muted/20 to-background/50">
                <div className="flex flex-col sm:flex-row gap-3">
                  <Textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder="Ask me anything... I'll provide comprehensive, fact-checked information with sources"
                    className="resize-none min-h-[60px] sm:min-h-[80px] max-h-32 sm:max-h-40 border-2 border-border/50 focus:border-primary/50 bg-background/80 text-sm sm:text-base"
                    disabled={isLoading}
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={!inputValue.trim() || isLoading}
                    className="gradient-primary shrink-0 h-[60px] sm:h-[80px] px-4 sm:px-6 w-full sm:w-auto"
                    size="icon"
                  >
                    {isLoading ? (
                      <Loader2 className="h-5 w-5 sm:h-6 sm:w-6 animate-spin" />
                    ) : (
                      <Send className="h-5 w-5 sm:h-6 sm:w-6" />
                    )}
                  </Button>
                </div>
                
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mt-4 gap-2 text-xs text-muted-foreground">
                  <p>Press Enter to send, Shift+Enter for new line</p>
                  <div className="flex items-center gap-3 sm:gap-4">
                    <span className="flex items-center gap-1">
                      <Shield className="h-2 w-2 sm:h-3 sm:w-3" />
                      Fact-checked responses
                    </span>
                    <span className="flex items-center gap-1">
                      <Zap className="h-2 w-2 sm:h-3 sm:w-3" />
                      Real-time research
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </PageLayout>
  );
}
