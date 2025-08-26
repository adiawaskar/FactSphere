
import { LucideIcon } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface StatsCardProps {
  title: string;
  value: string;
  description: string;
  trend: number;
  icon: LucideIcon;
}

export const StatsCard = ({ title, value, description, trend, icon: Icon }: StatsCardProps) => {
  const getTrendColor = () => {
    if (trend > 0) return 'text-verified';
    if (trend < 0) return 'text-danger';
    return 'text-muted-foreground';
  };

  const getTrendText = () => {
    if (trend > 0) return `+${trend}% from last month`;
    if (trend < 0) return `${trend}% from last month`;
    return 'No change from last month';
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground mb-1">
          {description}
        </p>
        <p className={`text-xs ${getTrendColor()}`}>
          {getTrendText()}
        </p>
      </CardContent>
    </Card>
  );
};
