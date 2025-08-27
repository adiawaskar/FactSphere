
import { BookOpen, Play, Users, Award, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const educationalContent = [
  {
    id: '1',
    title: 'Spotting Deepfakes: A Visual Guide',
    type: 'Interactive Tutorial',
    duration: '15 min',
    level: 'Beginner',
    description: 'Learn to identify AI-generated images and videos with practical examples.',
    icon: Play
  },
  {
    id: '2',
    title: 'Source Credibility Assessment',
    type: 'Course',
    duration: '45 min',
    level: 'Intermediate',
    description: 'Master the art of evaluating news sources and detecting bias.',
    icon: BookOpen
  },
  {
    id: '3',
    title: 'Media Literacy Challenge',
    type: 'Interactive Quiz',
    duration: '10 min',
    level: 'All Levels',
    description: 'Test your ability to distinguish real news from misinformation.',
    icon: Award
  }
];

export const EducationHub = () => {
  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold text-gradient">Learn to Spot Misinformation</h2>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          Develop critical thinking skills and learn practical techniques to identify 
          fake news, deepfakes, and misleading information.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {educationalContent.map((content) => (
          <Card key={content.id} className="hover:shadow-lg transition-shadow group">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="p-2 bg-primary/10 rounded-lg group-hover:bg-primary/20 transition-colors">
                  <content.icon className="h-5 w-5 text-primary" />
                </div>
                <Badge variant="outline">{content.level}</Badge>
              </div>
              <CardTitle className="text-lg">{content.title}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                {content.description}
              </p>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">{content.type}</span>
                <span className="font-medium">{content.duration}</span>
              </div>
              <Button className="w-full group-hover:bg-primary/90">
                Start Learning
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Tips */}
      <Card className="bg-gradient-to-r from-primary/5 to-secondary/5 border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Community Tips
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h4 className="font-semibold">Check Multiple Sources</h4>
              <p className="text-sm text-muted-foreground">
                Cross-reference information across different reputable news outlets
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold">Verify Before Sharing</h4>
              <p className="text-sm text-muted-foreground">
                Use fact-checking tools before sharing content on social media
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold">Look for Citations</h4>
              <p className="text-sm text-muted-foreground">
                Credible articles should cite authoritative sources and data
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold">Check Publication Dates</h4>
              <p className="text-sm text-muted-foreground">
                Ensure the information is current and not outdated
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
