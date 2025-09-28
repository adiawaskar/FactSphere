// frontend/src/components/layout/PageLayout.tsx
import { ReactNode } from 'react';
import { Header } from './Header';
import { BackgroundElements } from '@/components/ui/background-elements';
import { motion } from 'framer-motion';

interface PageLayoutProps {
  children: ReactNode;
  className?: string;
}

export const PageLayout = ({ children, className = '' }: PageLayoutProps) => {
  return (
    <div className="min-h-screen bg-background relative">
      <BackgroundElements />
      <Header />
      <motion.main 
        className={`container mx-auto px-4 sm:px-6 lg:px-8 relative z-10 ${className}`}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {children}
      </motion.main>
    </div>
  );
};
