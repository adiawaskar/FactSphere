
import React from 'react';
import { motion } from 'framer-motion';
import { PageLayout } from '@/components/layout/PageLayout';
import { useNotifications } from '@/contexts/NotificationsContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { 
  Bell, 
  CheckCircle, 
  AlertTriangle, 
  Info, 
  XCircle, 
  Clock,
  MailCheck,
  Trash2,
  ExternalLink
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';

const Notifications = () => {
  const { notifications, unreadCount, markAsRead, markAllAsRead, removeNotification } = useNotifications();
  const navigate = useNavigate();

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 sm:h-5 sm:w-5 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 sm:h-5 sm:w-5 text-red-500" />;
      default:
        return <Info className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500" />;
    }
  };

  const getNotificationBadge = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  const handleNotificationClick = (notification: any) => {
    if (!notification.read) {
      markAsRead(notification.id);
    }
    if (notification.actionUrl) {
      navigate(notification.actionUrl);
    }
  };

  return (
    <PageLayout>
      <div className="min-h-screen bg-gradient-to-br from-background via-background/95 to-muted/50">
        <div className="container mx-auto px-4 sm:px-6 py-6 sm:py-8 max-w-4xl">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 sm:mb-8"
          >
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Bell className="h-6 w-6 sm:h-8 sm:w-8 text-primary" />
                  {unreadCount > 0 && (
                    <Badge className="absolute -top-2 -right-2 h-4 w-4 sm:h-5 sm:w-5 rounded-full p-0 flex items-center justify-center text-xs bg-red-500 text-white">
                      {unreadCount}
                    </Badge>
                  )}
                </div>
                <div>
                  <h1 className="text-2xl sm:text-3xl font-bold text-gradient">Notifications</h1>
                  <p className="text-sm sm:text-base text-muted-foreground">
                    {notifications.length} total, {unreadCount} unread
                  </p>
                </div>
              </div>
              
              {unreadCount > 0 && (
                <Button 
                  onClick={markAllAsRead} 
                  variant="outline" 
                  className="gap-2 w-full sm:w-auto"
                  size="sm"
                >
                  <MailCheck className="h-4 w-4" />
                  <span className="sm:inline">Mark All Read</span>
                </Button>
              )}
            </div>
          </motion.div>

          {/* Notifications List */}
          <div className="space-y-3 sm:space-y-4">
            {notifications.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-8 sm:py-12"
              >
                <Bell className="h-12 w-12 sm:h-16 sm:w-16 text-muted-foreground/50 mx-auto mb-4" />
                <h3 className="text-lg sm:text-xl font-semibold text-muted-foreground mb-2">
                  No notifications yet
                </h3>
                <p className="text-sm sm:text-base text-muted-foreground px-4">
                  When you have new notifications, they'll appear here.
                </p>
              </motion.div>
            ) : (
              notifications.map((notification, index) => (
                <motion.div
                  key={notification.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card 
                    className={`transition-all duration-200 hover:shadow-md cursor-pointer ${
                      !notification.read 
                        ? 'border-primary/20 bg-primary/5 hover:bg-primary/10' 
                        : 'hover:bg-muted/50'
                    }`}
                  >
                    <CardContent className="p-4 sm:p-6">
                      <div className="flex items-start justify-between gap-3 sm:gap-4">
                        <div className="flex items-start gap-3 sm:gap-4 flex-1 min-w-0">
                          <div className="flex-shrink-0 mt-0.5 sm:mt-1">
                            {getNotificationIcon(notification.type)}
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-2">
                              <div className="flex items-center gap-2">
                                <h3 
                                  className={`font-semibold text-sm sm:text-base ${
                                    !notification.read ? 'text-foreground' : 'text-muted-foreground'
                                  }`}
                                >
                                  {notification.title}
                                </h3>
                                {!notification.read && (
                                  <div className="w-2 h-2 bg-primary rounded-full flex-shrink-0" />
                                )}
                              </div>
                              <Badge 
                                variant="outline" 
                                className={`text-xs w-fit ${getNotificationBadge(notification.type)}`}
                              >
                                {notification.type}
                              </Badge>
                            </div>
                            
                            <p className="text-xs sm:text-sm text-muted-foreground mb-3 leading-relaxed">
                              {notification.message}
                            </p>
                            
                            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-xs text-muted-foreground">
                              <div className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {formatDistanceToNow(notification.timestamp, { addSuffix: true })}
                              </div>
                              {notification.actionUrl && (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleNotificationClick(notification);
                                  }}
                                  className="flex items-center gap-1 text-primary hover:text-primary/80 transition-colors w-fit"
                                >
                                  <ExternalLink className="h-3 w-3" />
                                  View Details
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex flex-col sm:flex-row items-center gap-1 sm:gap-2 flex-shrink-0">
                          {!notification.read && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                markAsRead(notification.id);
                              }}
                              className="h-7 w-7 sm:h-8 sm:w-8 p-0"
                            >
                              <CheckCircle className="h-3 w-3 sm:h-4 sm:w-4" />
                            </Button>
                          )}
                          
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              removeNotification(notification.id);
                            }}
                            className="h-7 w-7 sm:h-8 sm:w-8 p-0 text-muted-foreground hover:text-destructive"
                          >
                            <Trash2 className="h-3 w-3 sm:h-4 sm:w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))
            )}
          </div>
        </div>
      </div>
    </PageLayout>
  );
};

export default Notifications;
