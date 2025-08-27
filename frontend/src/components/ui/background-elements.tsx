
import { motion } from 'framer-motion';

export const BackgroundElements = () => {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
      {/* Primary Blob */}
      <motion.div
        className="absolute top-20 left-10 w-72 h-72 bg-gradient-to-r from-primary/20 to-secondary/20 rounded-full blur-3xl"
        animate={{
          x: [0, 50, 0],
          y: [0, 30, 0],
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      
      {/* Secondary Blob */}
      <motion.div
        className="absolute top-1/3 right-10 w-96 h-96 bg-gradient-to-r from-warning/15 to-danger/15 rounded-full blur-3xl"
        animate={{
          x: [0, -30, 0],
          y: [0, 50, 0],
          scale: [1, 0.9, 1],
        }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      
      {/* Tertiary Blob */}
      <motion.div
        className="absolute bottom-20 left-1/4 w-80 h-80 bg-gradient-to-r from-verified/20 to-primary/20 rounded-full blur-3xl"
        animate={{
          x: [0, 40, 0],
          y: [0, -20, 0],
          scale: [1, 1.2, 1],
        }}
        transition={{
          duration: 30,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      
      {/* Quaternary Blob */}
      <motion.div
        className="absolute bottom-32 right-1/4 w-64 h-64 bg-gradient-to-r from-questionable/25 to-warning/25 rounded-full blur-3xl"
        animate={{
          x: [0, -25, 0],
          y: [0, 35, 0],
          scale: [1, 0.8, 1],
        }}
        transition={{
          duration: 18,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      
      {/* Small accent blobs */}
      <motion.div
        className="absolute top-1/2 left-1/2 w-32 h-32 bg-gradient-to-r from-secondary/30 to-verified/30 rounded-full blur-2xl"
        animate={{
          x: [0, 20, 0],
          y: [0, -15, 0],
          rotate: [0, 180, 360],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      
      <motion.div
        className="absolute top-3/4 left-3/4 w-40 h-40 bg-gradient-to-r from-danger/20 to-primary/20 rounded-full blur-2xl"
        animate={{
          x: [0, -30, 0],
          y: [0, 25, 0],
          rotate: [360, 180, 0],
        }}
        transition={{
          duration: 22,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
    </div>
  );
};
