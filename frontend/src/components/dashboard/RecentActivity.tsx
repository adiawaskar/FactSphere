// frontend/src/components/dashboard/RecentActivity.tsx
import { Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface ActivityItem {
  id: string;
  type: 'text' | 'url' | 'image';
  content: string;
  result: 'verified' | 'false' | 'questionable';
  timestamp: string;
  confidence: number;
}

const mockActivities: ActivityItem[] = [
  {
    id: '1',
    type: 'text',
    content: 'Climate change statistics claim verification',
    result: 'verified',
    timestamp: '2 hours ago',
    confidence: 92
  },
  {
    id: '2',
    type: 'url',
    content: 'News article about recent political developments',
    result: 'questionable',
    timestamp: '4 hours ago',
    confidence: 67
  },
  {
    id: '3',
    type: 'image',
    content: 'Social media image claiming historical facts',
    result: 'false',
    timestamp: '6 hours ago',
    confidence: 88
  }
];

export const RecentActivity = () => {
  const getResultIcon = (result: string) => {
    switch (result) {
      case 'verified': return <CheckCircle className="h-4 w-4 text-verified" />;
      case 'false': return <XCircle className="h-4 w-4 text-danger" />;
      case 'questionable': return <AlertTriangle className="h-4 w-4 text-warning" />;
      default: return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getResultColor = (result: string) => {
    switch (result) {
      case 'verified': return 'bg-verified/10 text-verified border-verified/20';
      case 'false': return 'bg-danger/10 text-danger border-danger/20';
      case 'questionable': return 'bg-warning/10 text-warning border-warning/20';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {mockActivities.map((activity) => (
            <div key={activity.id} className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
              <div className="mt-0.5">
                {getResultIcon(activity.result)}
              </div>
              <div className="flex-1 space-y-1">
                <p className="text-sm font-medium line-clamp-2">
                  {activity.content}
                </p>
                <div className="flex items-center gap-2">
                  <Badge 
                    variant="outline" 
                    className={`text-xs ${getResultColor(activity.result)}`}
                  >
                    {activity.result}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {activity.confidence}% confidence
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {activity.timestamp}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
