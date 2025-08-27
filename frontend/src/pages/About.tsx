
import { PageLayout } from '@/components/layout/PageLayout';
import { Card, CardContent } from '@/components/ui/card';
import { Shield, Target, Users, Award, Zap, Globe } from 'lucide-react';
import { motion } from 'framer-motion';
import { useInView } from 'react-intersection-observer';

const features = [
  {
    icon: Shield,
    title: 'Advanced AI Detection',
    description: 'State-of-the-art machine learning algorithms trained on millions of data points to identify misinformation with high accuracy.'
  },
  {
    icon: Zap,
    title: 'Real-time Analysis',
    description: 'Lightning-fast processing that provides instant results without compromising on accuracy or depth of analysis.'
  },
  {
    icon: Globe,
    title: 'Multi-platform Monitoring',
    description: 'Comprehensive coverage across social media platforms, news sites, and other digital information sources.'
  },
  {
    icon: Target,
    title: 'Precision Scoring',
    description: 'Detailed credibility scoring system that provides nuanced analysis rather than simple true/false judgments.'
  }
];

const team = [
  {
    name: 'Dr. Sarah Chen',
    role: 'Chief AI Scientist',
    description: 'Former MIT researcher specializing in natural language processing and misinformation detection.'
  },
  {
    name: 'Michael Rodriguez',
    role: 'Lead Engineer',
    description: 'Full-stack developer with expertise in scalable AI systems and real-time data processing.'
  },
  {
    name: 'Dr. Aisha Patel',
    role: 'Research Director',
    description: 'Computational linguist focused on cross-cultural misinformation patterns and detection.'
  }
];

export default function About() {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  return (
    <PageLayout className="py-8">
      <motion.div
        ref={ref}
        initial={{ opacity: 0, y: 50 }}
        animate={inView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.6 }}
        className="space-y-16"
      >
        {/* Hero Section */}
        <div className="text-center space-y-6">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full"
          >
            <Shield className="h-5 w-5 text-primary" />
            <span className="text-primary font-medium">About TruthGuard AI</span>
          </motion.div>
          
          <motion.h1 
            className="text-4xl md:text-6xl font-bold text-gradient"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            Fighting Misinformation
            <br />
            <span className="text-secondary">with AI</span>
          </motion.h1>
          
          <motion.p 
            className="text-xl text-muted-foreground max-w-3xl mx-auto"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            We're on a mission to create a more informed world by providing cutting-edge AI tools 
            that help identify, analyze, and combat misinformation across digital platforms.
          </motion.p>
        </div>

        {/* Mission Statement */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="text-center"
        >
          <Card className="glass-card max-w-4xl mx-auto">
            <CardContent className="p-8">
              <h2 className="text-3xl font-bold mb-6">Our Mission</h2>
              <p className="text-lg text-muted-foreground leading-relaxed">
                In an era where information travels faster than ever before, the ability to distinguish 
                fact from fiction has become crucial. TruthGuard AI leverages advanced artificial intelligence 
                to provide real-time, accurate analysis of digital content, empowering individuals and 
                organizations to make informed decisions based on verified information.
              </p>
            </CardContent>
          </Card>
        </motion.div>

        {/* Features Grid */}
        <div className="space-y-8">
          <motion.h2
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="text-3xl font-bold text-center"
          >
            What Makes Us Different
          </motion.h2>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7 + index * 0.1 }}
                  whileHover={{ scale: 1.05 }}
                >
                  <Card className="glass-card h-full hover:shadow-lg transition-shadow">
                    <CardContent className="p-6 text-center">
                      <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Icon className="h-6 w-6 text-primary" />
                      </div>
                      <h3 className="font-semibold mb-2">{feature.title}</h3>
                      <p className="text-sm text-muted-foreground">
                        {feature.description}
                      </p>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Team Section */}
        <div className="space-y-8">
          <motion.h2
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="text-3xl font-bold text-center"
          >
            Meet Our Team
          </motion.h2>
          
          <div className="grid md:grid-cols-3 gap-6">
            {team.map((member, index) => (
              <motion.div
                key={member.name}
                initial={{ opacity: 0, y: 50 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.9 + index * 0.1 }}
                whileHover={{ scale: 1.05 }}
              >
                <Card className="glass-card hover:shadow-lg transition-shadow">
                  <CardContent className="p-6 text-center">
                    <div className="w-16 h-16 bg-gradient-primary rounded-full mx-auto mb-4 flex items-center justify-center">
                      <Users className="h-8 w-8 text-white" />
                    </div>
                    <h3 className="font-semibold text-lg">{member.name}</h3>
                    <p className="text-primary text-sm mb-3">{member.role}</p>
                    <p className="text-sm text-muted-foreground">
                      {member.description}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Stats Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.0 }}
        >
          <Card className="glass-card">
            <CardContent className="p-8">
              <div className="grid md:grid-cols-4 gap-8 text-center">
                <div>
                  <motion.div
                    className="text-3xl font-bold text-primary mb-2"
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 1.2 }}
                  >
                    1M+
                  </motion.div>
                  <p className="text-muted-foreground">Content Analyzed</p>
                </div>
                <div>
                  <motion.div
                    className="text-3xl font-bold text-secondary mb-2"
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 1.3 }}
                  >
                    98.5%
                  </motion.div>
                  <p className="text-muted-foreground">Accuracy Rate</p>
                </div>
                <div>
                  <motion.div
                    className="text-3xl font-bold text-warning mb-2"
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 1.4 }}
                  >
                    50K+
                  </motion.div>
                  <p className="text-muted-foreground">Active Users</p>
                </div>
                <div>
                  <motion.div
                    className="text-3xl font-bold text-verified mb-2"
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 1.5 }}
                  >
                    24/7
                  </motion.div>
                  <p className="text-muted-foreground">Monitoring</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </PageLayout>
  );
}
