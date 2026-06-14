import React from 'react';
import { motion } from 'motion/react';

interface AthanorIconProps {
  className?: string;
  style?: React.CSSProperties;
}

export const AthanorIcon: React.FC<AthanorIconProps> = ({ className, style }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    style={{ overflow: 'visible', ...style }}
  >
    {/* 1. Cauldron Structure - Bottom layers with thicker profile */}
    <path d="M 4.5 6.5 C 6.5 9 2.5 13.5 4 16.5 C 5 18.5 8 19.5 12 19.5 C 16 19.5 19 18.5 20 16.5 C 21.5 13.5 17.5 9 19.5 6.5" stroke="currentColor" strokeWidth="1.6" fill="white" strokeLinecap="round" />
    <path d="M 4.5 6.5 A 7.5 1.4 0 0 1 19.5 6.5" stroke="currentColor" strokeWidth="1.6" fill="none" />
    
    {/* Robust integrated side handles */}
    <g stroke="currentColor" strokeWidth="1.5">
      <path d="M 3.8 9.5 A 1.8 1.8 0 1 0 3.8 12" fill="none" />
      <path d="M 20.2 9.5 A 1.8 1.8 0 1 1 20.2 12" fill="none" />
    </g>
    
    {/* 2. Vibrant Layered Flame - Fluid "Power Source" form with transformation energy */}
    <motion.g 
      animate={{ 
        scaleY: [1, 1.05, 1], 
        y: [-6.5, -6.9, -6.5],
        opacity: [0.9, 0.95, 0.9]
      }}
      transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
      style={{ originX: "50%", originY: "21.8px" }}
    >
      <g transform="translate(0, -6.5)">
        {/* Transformation Light - Cyan energy core pointing UP */}
        <path d="M12 21.8 
                C 11.2 21.8 11.0 19.0 11.5 16.0 
                C 11.8 17.5 11.9 16.0 12 11.5 
                C 12.1 16.0 12.2 17.5 12.5 16.0 
                C 13.0 19.0 12.8 21.8 12 21.8 Z" fill="#22d3ee" opacity="0.7" stroke="none" />
        
        {/* Red Layer - Vibrant Flame Base */}
        <path d="M12 21.8 
                C 8.5 21.8 7.5 19.5 9.5 14.5 
                C 10.5 16.5 11.2 16.0 12 11.0 
                C 12.8 16.0 13.5 16.5 14.5 14.5 
                C 16.5 19.5 15.5 21.8 12 21.8 Z" fill="#ef4444" opacity="0.8" stroke="none" />
        {/* Orange Layer - Intense Heat */}
        <path d="M12 21.8 
                C 9.5 21.8 9.0 20.0 10.5 16.0 
                C 11.2 17.5 11.5 17.0 12 12.5 
                C 12.5 17.0 12.8 17.5 13.5 16.0 
                C 15.0 20.0 14.5 21.8 12 21.8 Z" fill="#fb923c" opacity="0.9" stroke="none" />
        {/* Yellow Layer - White-Hot Energy */}
        <path d="M12 21.8 
                C 10.5 21.8 10.0 20.8 11.0 18.0 
                C 11.5 19.0 11.7 18.5 12 15.5 
                C 12.3 18.5 12.5 19.0 13.0 18.0 
                C 14.0 20.8 13.5 21.8 12 21.8 Z" fill="#fef08a" opacity="1" stroke="none" />
      </g>
    </motion.g>

    {/* 3. Front Rim - Defines the opening, behind documents */}
    <path d="M 19.5 6.5 A 7.5 1.4 0 0 1 4.5 6.5" stroke="currentColor" strokeWidth="1.6" fill="none" />
    <ellipse cx="12" cy="6.5" rx="7.5" ry="1.4" stroke="none" fill="currentColor" opacity="0.05" />

    {/* 4. Falling Documents - Precision 10s Orbital Motion with differentiated paths to prevent overlap */}
    <g strokeWidth="1.2" strokeLinejoin="round" strokeLinecap="round" fill="none">
      {/* The static group below defines the Orbital Center (initially 12, 6.5, moved up to 2.0) */}
      <g transform="translate(12, 2.0)">
        {/* Doc 1 - Red (Outer Orbit, slightly higher vertical offset) */}
        <motion.g 
          animate={{ 
            x: [4.5, 0, -8.5, 0, 4.5], // Differentiated X path
            y: [0.3, 1.8, 0.3, -1.2, 0.3], 
            scale: [1.1, 1.35, 1, 0.7, 1.1],
            opacity: [1, 1, 0.8, 0.4, 1],
            rotate: [-12, 0, 12, 0, -12]
          }}
          transition={{ 
            duration: 10, 
            repeat: Infinity, 
            ease: "linear" 
          }}
        >
          <g transform="translate(0, -1.2)"> {/* Increased vertical separation */}
            <path d="M-1.2 -1.9 h 1.8 l 1.0 1.0 v 3.2 a 0.4 0.4 0 0 1 -0.4 0.4 h -2.4 a 0.4 0.4 0 0 1 -0.4 -0.4 v -3.8 a 0.4 0.4 0 0 1 0.4 -0.4" fill="white" stroke="#ef4444" />
            <path d="M-1.2 1.7 h 2.4 a 0.4 0.4 0 0 1 0.4 0.4 v 0.1 h -3.2 v -0.1 a 0.4 0.4 0 0 1 0.4 -0.4" fill="#fbbf24" stroke="none" opacity="1" />
            <path d="M-0.3 0.8 h 1.2 M-0.3 1.8 h 0.8" stroke="#ef4444" strokeWidth="0.8" opacity="0.9" />
          </g>
        </motion.g>

        {/* Doc 2 - Blue (Inner Orbit, slightly lower vertical offset, 180 degrees sync) */}
        <motion.g 
          animate={{ 
            x: [-7.0, 0, 3.5, 0, -7.0], // Different Rx and phase offset handled by the sequence
            y: [-0.3, -1.0, -0.3, 1.6, -0.3], 
            scale: [0.85, 0.65, 0.85, 1.3, 0.85],
            opacity: [0.7, 0.4, 0.7, 1, 0.7],
            rotate: [12, 0, -12, 0, 12]
          }}
          transition={{ 
            duration: 10, 
            repeat: Infinity, 
            ease: "linear"
          }}
        >
          <g transform="translate(0, 0.8)"> {/* Increased vertical separation */}
            <path d="M-1.2 -1.9 h 1.8 l 1.0 1.0 v 3.2 a 0.4 0.4 0 0 1 -0.4 0.4 h -2.4 a 0.4 0.4 0 0 1 -0.4 -0.4 v -3.8 a 0.4 0.4 0 0 1 0.4 -0.4" fill="white" stroke="#3b82f6" />
            <path d="M-1.2 1.7 h 2.4 a 0.4 0.4 0 0 1 0.4 0.4 v 0.1 h -3.2 v -0.1 a 0.4 0.4 0 0 1 0.4 -0.4" fill="#fbbf24" stroke="none" opacity="1" />
            <path d="M-0.3 0.8 h 1.2 M-0.3 1.8 h 0.8" stroke="#3b82f6" strokeWidth="0.8" opacity="0.9" />
          </g>
        </motion.g>
      </g>
    </g>

    {/* 5. Simplified Details - Bold Yin Yang and Robust Legs */}
    <g transform="translate(12 14.5)" opacity="0.25">
      <circle r="2.2" fill="none" stroke="currentColor" strokeWidth="1.2" />
      <path d="M 0 -2.2 A 1.1 1.1 0 0 1 0 0 A 1.1 1.1 0 0 0 0 2.2 A 2.2 2.2 0 0 1 0 -2.2" fill="currentColor" />
    </g>
    
    <g stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" fill="none">
      <path d="M 7 19 L 5.5 22.2" />
      <path d="M 17 19 L 18.5 22.2" />
      <path d="M 12 19.5 V 22.7" />
    </g>

  </svg>
);
