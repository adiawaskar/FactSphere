
import { Shield, Bell, User, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Navigation } from './Navigation';
import { motion } from 'framer-motion';

export const Header = () => {
  return (
    <motion.header 
      className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="container flex h-16 items-center justify-between gap-4 px-0">

        {/* Logo */}
        <motion.div 
          className="flex items-center gap-2 lg:gap-3 min-w-0"
          whileHover={{ scale: 1.05 }}
        >
          <div className="relative">
            <Shield className="h-6 w-6 lg:h-8 lg:w-8 text-primary" />
            <motion.div 
              className="absolute -top-1 -right-1 w-2 h-2 lg:w-3 lg:h-3 bg-secondary rounded-full"
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          </div>
          <div className="flex flex-col min-w-0">
            <h1 className="text-lg lg:text-xl font-bold text-gradient truncate">TruthGuard</h1>
            <p className="text-xs text-muted-foreground hidden sm:block">Advanced Verification</p>
          </div>
        </motion.div>

        {/* Navigation */}
        <Navigation />

        {/* Search Bar - Hidden on small screens, shown on large */}
        <div className="hidden xl:flex flex-1 max-w-md ">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Quick check..."
              className="pl-10 bg-muted/50 border-0 focus-visible:ring-1"
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="hidden md:flex items-center gap-1 lg:gap-2">
          <Button variant="ghost" size="icon" className="h-9 w-9">
            <Bell className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-9 w-9">
            <User className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </motion.header>
  );
};
