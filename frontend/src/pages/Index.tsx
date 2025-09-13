//frontend/src/pages/Index.tsx
import { PageLayout } from '@/components/layout/PageLayout';
import { InputForm } from '@/components/analysis/InputForm';
import { AnalysisResults } from '@/components/analysis/AnalysisResults';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { RecentActivity } from '@/components/dashboard/RecentActivity';
import { EducationHub } from '@/components/education/EducationHub';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Shield, Zap, Eye, TrendingUp, Bot, Brain, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useState } from 'react';
import { useInView } from 'react-intersection-observer';

const features = [
  {
    icon: Eye,
    title: 'Deepfake Detection',
    description: 'Advanced AI to detect synthetic media and manipulated images',
    link: '/deepfake-detection',
    gradient: 'from-primary/20 to-secondary/20'
  },
  {
    icon: TrendingUp,
    title: 'Social Trends',
    description: 'Monitor misinformation spread across social platforms',
    link: '/social-trends',
    gradient: 'from-warning/20 to-danger/20'
  },
  {
    icon: Bot,
    title: 'AI Analyzer',
    description: 'Comprehensive fact-checking for any content type',
    link: '/ai-analyzer',
    gradient: 'from-verified/20 to-primary/20'
  },
  {
    icon: Brain,
    title: 'Knowledge Base',
    description: 'Learn about misinformation and digital literacy',
    link: '/knowledge-base',
    gradient: 'from-questionable/20 to-warning/20'
  }
];

export default function Index() {
  const [analysisData, setAnalysisData] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  const [heroRef, heroInView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });
  
  const [featuresRef, featuresInView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const handleAnalyze = async (data: any) => {
    console.log('Analyzing:', data);
    setIsAnalyzing(true);
    
    // Simulate analysis
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Mock result
    const mockResult = {
      verdict: Math.random() > 0.5 ? 'verified' : 'questionable',
      confidence: Math.floor(Math.random() * 30) + 70,
      sources: [
        { name: 'Reuters', credibility: 95, url: 'https://reuters.com' },
        { name: 'AP News', credibility: 92, url: 'https://apnews.com' }
      ],
      analysis: 'Based on cross-reference with multiple verified sources...'
    };
    
    setAnalysisData(mockResult);
    setIsAnalyzing(false);
  };

  return (
    <PageLayout>
      {/* Hero Section */}
      <motion.section 
        ref={heroRef}
        initial={{ opacity: 0, y: 50 }}
        animate={heroInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.8 }}
        className="py-12 md:py-20 text-center space-y-6 md:space-y-8"
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
          className="inline-flex items-center gap-2 px-4 md:px-6 py-2 md:py-3 bg-primary/10 rounded-full"
        >
          <Shield className="h-4 w-4 md:h-5 md:w-5 text-primary" />
          <span className="text-primary font-medium text-sm md:text-base">AI-Powered Truth Detection</span>
        </motion.div>
        
        <motion.h1 
          className="text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-bold leading-tight px-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          Fight <span className="text-gradient">Misinformation</span>
          <br />
          with <span className="text-secondary">AI Precision</span>
        </motion.h1>
        
        <motion.p 
          className="text-lg md:text-xl lg:text-2xl text-muted-foreground max-w-4xl mx-auto px-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          Advanced artificial intelligence that analyzes, verifies, and protects against 
          misinformation across all digital platforms in real-time.
        </motion.p>
        
        <motion.div
          className="flex flex-col sm:flex-row gap-3 md:gap-4 justify-center items-center px-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
        >
          <Button size="lg" className="gradient-primary hover:opacity-90 px-6 md:px-8 py-3 w-full sm:w-auto">
            <Zap className="mr-2 h-4 w-4 md:h-5 md:w-5" />
            Start Verification
          </Button>
          <Button variant="outline" size="lg" className="px-6 md:px-8 py-3 w-full sm:w-auto" asChild>
            <Link to="/about">
              Learn More
              <ArrowRight className="ml-2 h-4 w-4 md:h-5 md:w-5" />
            </Link>
          </Button>
        </motion.div>
      </motion.section>

      {/* Features Grid */}
      <motion.section
        ref={featuresRef}
        initial={{ opacity: 0, y: 50 }}
        animate={featuresInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.8 }}
        className="py-12 md:py-16 space-y-8 md:space-y-12"
      >
        <div className="text-center space-y-4 px-4">
          <h2 className="text-2xl md:text-3xl lg:text-4xl font-bold">Comprehensive Protection</h2>
          <p className="text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto">
            Multiple AI-powered tools to combat different types of misinformation
          </p>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 50 }}
                animate={featuresInView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: index * 0.2 }}
                whileHover={{ scale: 1.05, y: -5 }}
              >
                <Link to={feature.link}>
                  <Card className="glass-card h-full hover:shadow-xl transition-all duration-300 group border-2 border-transparent hover:border-primary/20">
                    <CardContent className="p-4 md:p-6 text-center">
                      <motion.div 
                        className={`w-12 h-12 md:w-16 md:h-16 bg-gradient-to-r ${feature.gradient} rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform`}
                        whileHover={{ rotate: 360 }}
                        transition={{ duration: 0.5 }}
                      >
                        <Icon className="h-6 w-6 md:h-8 md:w-8 text-primary" />
                      </motion.div>
                      <h3 className="font-semibold text-base md:text-lg mb-2">{feature.title}</h3>
                      <p className="text-sm md:text-base text-muted-foreground mb-4">{feature.description}</p>
                      <div className="flex items-center justify-center text-primary group-hover:text-secondary transition-colors">
                        <span className="text-sm font-medium">Explore</span>
                        <ArrowRight className="ml-1 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </motion.section>

      {/* Quick Analysis Section */}
      <section className="py-12 md:py-16 space-y-6 md:space-y-8">
        <div className="text-center space-y-4 px-4">
          <h2 className="text-2xl md:text-3xl lg:text-4xl font-bold">Quick Verification</h2>
          <p className="text-lg md:text-xl text-muted-foreground">
            Test our AI-powered analysis with any content
          </p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <InputForm onAnalyze={handleAnalyze} isAnalyzing={isAnalyzing} />
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <AnalysisResults data={analysisData} isLoading={isAnalyzing} />
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 md:py-16">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6"
        >
          <StatsCard
            title="Content Analyzed"
            value="2.1M+"
            description="Pieces of content verified"
            trend={12}
            icon={Shield}
          />
          <StatsCard
            title="Accuracy Rate"
            value="98.7%"
            description="Precision in detection"
            trend={2.3}
            icon={Zap}
          />
          <StatsCard
            title="Active Users"
            value="50K+"
            description="Trust our platform"
            trend={18}
            icon={Eye}
          />
        </motion.div>
      </section>

      {/* Recent Activity */}
      <section className="py-12 md:py-16">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <RecentActivity />
        </motion.div>
      </section>

      {/* Education Hub */}
      <section className="py-12 md:py-16 pb-20">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <EducationHub />
        </motion.div>
      </section>
    </PageLayout>
  );
}
