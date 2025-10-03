// frontend/src/contexts/NotificationsContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: Date;
  read: boolean;
  actionUrl?: string;
}

interface NotificationsContextType {
  notifications: Notification[];
  unreadCount: number;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  removeNotification: (id: string) => void;
}

const NotificationsContext = createContext<NotificationsContextType | undefined>(undefined);

export const useNotifications = () => {
  const context = useContext(NotificationsContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationsProvider');
  }
  return context;
};

export const NotificationsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([
    {
      id: '1',
      title: 'Analysis Complete',
      message: 'Your deepfake detection analysis has been completed successfully.',
      type: 'success',
      timestamp: new Date(Date.now() - 2 * 60 * 1000),
      read: false,
      actionUrl: '/deepfake-detection'
    },
    {
      id: '2',
      title: 'New Trending Topic',
      message: 'A new misinformation trend has been detected in your monitored topics.',
      type: 'warning',
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      read: false,
      actionUrl: '/social-trends'
    },
    {
      id: '3',
      title: 'Weekly Report Ready',
      message: 'Your weekly fact-checking report is now available for download.',
      type: 'info',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),  
      read: true,
      actionUrl: '/knowledge-base'
    },
    {
      id: '4',
      title: 'Security Alert',
      message: 'Suspicious activity detected in your account. Please review your recent activity.',
      type: 'error',
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000),
      read: false
    }
  ]);

  const unreadCount = notifications.filter(n => !n.read).length;

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === id 
          ? { ...notification, read: true }
          : notification
      )
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(notification => ({ ...notification, read: true }))
    );
  };

  const addNotification = (notificationData: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notificationData,
      id: Date.now().toString(),
      timestamp: new Date(),
      read: false
    };
    setNotifications(prev => [newNotification, ...prev]);
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  };

  return (
    <NotificationsContext.Provider value={{
      notifications,
      unreadCount,
      markAsRead,
      markAllAsRead,
      addNotification,
      removeNotification
    }}>
      {children}
    </NotificationsContext.Provider>
  );
};
