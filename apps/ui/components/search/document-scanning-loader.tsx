"use client";

import { motion } from "framer-motion";
import { FileText, Sparkles } from "lucide-react";

interface DocumentScanningLoaderProps {
  message?: string;
}

export function DocumentScanningLoader({ message = "Searching through documents..." }: DocumentScanningLoaderProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 space-y-6">
      {/* Animated document cards */}
      <div className="relative w-64 h-48">
        {[0, 1, 2, 3].map((index) => (
          <motion.div
            key={index}
            className="absolute inset-0 flex items-center justify-center"
            initial={{ opacity: 0, scale: 0.8, rotate: 0, y: 0 }}
            animate={{
              opacity: [0, 0.4, 0.7, 0.4, 0],
              scale: [0.8, 0.9, 1, 0.9, 0.8],
              rotate: [0, -2, 2, -2, 0],
              y: [0, -10, -20, -10, 0],
            }}
            transition={{
              duration: 3,
              delay: index * 0.3,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            <div className="bg-gradient-to-br from-primary/20 to-primary/5 border-2 border-primary/30 rounded-lg p-6 w-48 h-32 shadow-lg backdrop-blur-sm">
              <FileText className="w-8 h-8 text-primary/60 mb-2" />
              <div className="space-y-2">
                <div className="h-2 bg-primary/20 rounded w-full" />
                <div className="h-2 bg-primary/20 rounded w-3/4" />
                <div className="h-2 bg-primary/20 rounded w-5/6" />
              </div>
            </div>
          </motion.div>
        ))}

        {/* Scanning beam effect */}
        <motion.div
          className="absolute inset-0 flex items-center justify-center pointer-events-none"
          initial={{ opacity: 0 }}
          animate={{ opacity: [0, 1, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          <div className="w-full h-1 bg-gradient-to-r from-transparent via-primary to-transparent" />
        </motion.div>

        {/* Sparkle effect */}
        <motion.div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
          animate={{
            scale: [1, 1.2, 1],
            rotate: [0, 180, 360],
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "linear",
          }}
        >
          <Sparkles className="w-6 h-6 text-primary/40" />
        </motion.div>
      </div>

      {/* Loading message */}
      <div className="text-center space-y-2">
        <motion.p
          className="text-sm font-medium text-foreground"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          {message}
        </motion.p>

        {/* Animated dots */}
        <div className="flex justify-center space-x-1">
          {[0, 1, 2].map((index) => (
            <motion.div
              key={index}
              className="w-2 h-2 bg-primary rounded-full"
              animate={{
                scale: [1, 1.5, 1],
                opacity: [0.3, 1, 0.3],
              }}
              transition={{
                duration: 1.5,
                delay: index * 0.2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
