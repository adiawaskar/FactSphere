
import { useState } from 'react';
import { PageLayout } from '@/components/layout/PageLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Brain, Search, BookOpen, Lightbulb, ArrowRight, Clock, Users } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useInView } from 'react-intersection-observer';

interface Article {
  id: string;
  title: string;
  category: string;
  summary: string;
  readTime: string;
  popularity: number;
  tags: string[];
}

const mockArticles: Article[] = [
  {
    id: '1',
    title: 'Understanding Deepfakes: How AI Creates Synthetic Media',
    category: 'Technology',
    summary: 'A comprehensive guide to deepfake technology, how it works, and how to identify synthetic media.',
    readTime: '8 min read',
    popularity: 1250,
    tags: ['AI', 'Deepfakes', 'Media Literacy']
  },
  {
    id: '2',
    title: 'The Psychology of Misinformation: Why False Information Spreads',
    category: 'Psychology',
    summary: 'Explore the cognitive biases and psychological factors that make misinformation so effective.',
    readTime: '12 min read',
    popularity: 980,
    tags: ['Psychology', 'Misinformation', 'Cognitive Bias']
  },
  {
    id: '3',
    title: 'Fact-Checking Best Practices: A Step-by-Step Guide',
    category: 'Education',
    summary: 'Learn professional fact-checking techniques used by journalists and researchers.',
    readTime: '10 min read',
    popularity: 750,
    tags: ['Fact-checking', 'Research', 'Verification']
  },
  {
    id: '4',
    title: 'Social Media Algorithms and Information Bubbles',
    category: 'Technology',
    summary: 'How recommendation algorithms can create echo chambers and spread misinformation.',
    readTime: '6 min read',
    popularity: 650,
    tags: ['Social Media', 'Algorithms', 'Echo Chambers']
  }
];

export default function KnowledgeBase() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const categories = ['all', 'Technology', 'Psychology', 'Education', 'Politics', 'Health'];

  const filteredArticles = mockArticles.filter(article => {
    const matchesSearch = article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         article.summary.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || article.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

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
            className="inline-flex items-center gap-2 px-4 py-2 bg-verified/10 rounded-full"
          >
            <Brain className="h-5 w-5 text-verified" />
            <span className="text-verified font-medium">Educational Resources</span>
          </motion.div>
          
          <motion.h1 
            className="text-4xl md:text-6xl font-bold text-gradient"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            Knowledge Base
          </motion.h1>
          
          <motion.p 
            className="text-xl text-muted-foreground max-w-2xl mx-auto"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            Learn about misinformation, fact-checking techniques, and digital literacy from expert-curated content
          </motion.p>
        </div>

        {/* Search and Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="space-y-4"
        >
          <div className="relative max-w-md mx-auto">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search articles..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          
          <div className="flex flex-wrap justify-center gap-2">
            {categories.map((category) => (
              <Button
                key={category}
                variant={selectedCategory === category ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedCategory(category)}
                className="capitalize"
              >
                {category}
              </Button>
            ))}
          </div>
        </motion.div>

        {/* Featured Topics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="grid md:grid-cols-3 gap-6"
        >
          <Card className="glass-card hover:shadow-lg transition-shadow">
            <CardContent className="p-6 text-center">
              <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <BookOpen className="h-6 w-6 text-primary" />
              </div>
              <h3 className="font-semibold mb-2">Media Literacy</h3>
              <p className="text-sm text-muted-foreground">
                Essential skills for navigating today's information landscape
              </p>
            </CardContent>
          </Card>
          
          <Card className="glass-card hover:shadow-lg transition-shadow">
            <CardContent className="p-6 text-center">
              <div className="w-12 h-12 bg-secondary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Lightbulb className="h-6 w-6 text-secondary" />
              </div>
              <h3 className="font-semibold mb-2">Critical Thinking</h3>
              <p className="text-sm text-muted-foreground">
                Develop analytical skills to evaluate information sources
              </p>
            </CardContent>
          </Card>
          
          <Card className="glass-card hover:shadow-lg transition-shadow">
            <CardContent className="p-6 text-center">
              <div className="w-12 h-12 bg-warning/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Brain className="h-6 w-6 text-warning" />
              </div>
              <h3 className="font-semibold mb-2">AI & Technology</h3>
              <p className="text-sm text-muted-foreground">
                Understanding how AI creates and detects misinformation
              </p>
            </CardContent>
          </Card>
        </motion.div>

        {/* Articles Grid */}
        <div className="space-y-6">
          <motion.h2
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
            className="text-2xl font-bold"
          >
            Latest Articles
          </motion.h2>
          
          <div className="grid gap-6">
            <AnimatePresence>
              {filteredArticles.map((article, index) => (
                <motion.div
                  key={article.id}
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -50 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ scale: 1.02 }}
                >
                  <Card className="glass-card hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="space-y-2 flex-1">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{article.category}</Badge>
                            <div className="flex items-center gap-1 text-sm text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              {article.readTime}
                            </div>
                            <div className="flex items-center gap-1 text-sm text-muted-foreground">
                              <Users className="h-3 w-3" />
                              {article.popularity} readers
                            </div>
                          </div>
                          <CardTitle className="hover:text-primary transition-colors cursor-pointer">
                            {article.title}
                          </CardTitle>
                        </div>
                        <Button variant="ghost" size="icon">
                          <ArrowRight className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardHeader>
                    
                    <CardContent>
                      <p className="text-muted-foreground mb-4">{article.summary}</p>
                      
                      <div className="flex flex-wrap gap-2">
                        {article.tags.map((tag) => (
                          <Badge key={tag} variant="secondary" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </motion.div>
    </PageLayout>
  );
}
