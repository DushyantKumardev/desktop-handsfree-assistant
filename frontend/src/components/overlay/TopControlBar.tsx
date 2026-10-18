import React from 'react';
import { motion } from 'framer-motion';
import { ChevronsDown } from 'lucide-react';

interface TopControlBarProps {
  onMinimize: () => void;
}

export const TopControlBar: React.FC<TopControlBarProps> = ({ onMinimize }) => {
  return (
    <motion.div
      id="top-control-bar"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 6 }}
      className="shrink-0 flex justify-center mb-1 cursor-grab"
    >
      <button
        onClick={onMinimize}
        className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 hover:text-zinc-100 text-[11px] font-medium tracking-tight shadow-md transition-all select-none"
        type="button"
        title="Minimize overlay"
      >
        <ChevronsDown className="w-3 h-3 text-white/50" />
        <span>Minimize</span>
      </button>
    </motion.div>
  );
};
