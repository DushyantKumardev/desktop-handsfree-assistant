import React from "react";
import { motion } from "framer-motion";

interface GeminiWaveformProps {
  color?: string;
  barCount?: number;
}

// Target height sets for smooth oscillating wave motion
const WAVE_PATTERNS = [
  [4, 8, 14, 20, 26, 22, 16, 24, 28, 20, 14, 22, 16, 10, 6, 4],
  [6, 12, 22, 28, 18, 12, 26, 30, 22, 16, 24, 18, 12, 8, 4, 3],
  [3, 6, 10, 16, 24, 30, 22, 14, 18, 26, 20, 14, 8, 6, 4, 3],
  [4, 10, 18, 24, 16, 22, 28, 24, 18, 12, 20, 26, 14, 8, 5, 3],
];

export const GeminiWaveform: React.FC<GeminiWaveformProps> = ({
  color = "var(--content-primary)",
  barCount = 16,
}) => {
  return (
    <div className="flex items-center justify-center gap-[3px] h-8 px-2 overflow-hidden select-none">
      {Array.from({ length: barCount }).map((_, i) => {
        const h0 = WAVE_PATTERNS[0][i % WAVE_PATTERNS[0].length];
        const h1 = WAVE_PATTERNS[1][i % WAVE_PATTERNS[1].length];
        const h2 = WAVE_PATTERNS[2][i % WAVE_PATTERNS[2].length];
        const h3 = WAVE_PATTERNS[3][i % WAVE_PATTERNS[3].length];

        return (
          <motion.span
            key={i}
            className="w-[3px] rounded-full"
            style={{ backgroundColor: color }}
            initial={{ height: 4 }}
            animate={{
              height: [h0, h1, h2, h3, h0],
            }}
            transition={{
              duration: 1.2,
              repeat: Infinity,
              ease: "easeInOut",
              delay: (i * 0.06) % 0.4,
            }}
          />
        );
      })}
    </div>
  );
};
