import React from 'react';
import { motion } from 'framer-motion';

const BARS = [0.3, 0.65, 0.9, 0.5, 1.0, 0.7, 0.4, 0.85, 0.55, 0.35, 0.75];

export const AudioWaveform: React.FC = () => (
  <div className="flex items-center gap-[2.5px] h-5 select-none pointer-events-none">
    {BARS.map((scale, i) => (
      <motion.span
        key={i}
        className="w-[2px] rounded-full"
        style={{
          background: `linear-gradient(to top, #f59e0b, #fb923c, #f97316)`,
          minHeight: 2,
        }}
        animate={{ height: ['15%', `${scale * 100}%`, '18%'] }}
        transition={{
          duration: 0.5 + (i % 4) * 0.15,
          repeat: Infinity,
          repeatType: 'mirror',
          ease: 'easeInOut',
          delay: i * 0.06,
        }}
      />
    ))}
  </div>
);
