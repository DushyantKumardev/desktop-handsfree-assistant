import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Copy, Check, X } from "lucide-react";
import type { AssistantResponse } from "../../types/assistant";

// Spring config for the card entrance — feels physical, not linear
const ENTER_SPRING = { type: "spring", stiffness: 380, damping: 32, mass: 0.9 } as const;
const EXIT_EASE   = { duration: 0.2, ease: [0.4, 0, 1, 1] } as const;

interface ResponseCardProps {
  response: AssistantResponse;
  onClose?: () => void;
}

export const ResponseCard: React.FC<ResponseCardProps> = ({ response, onClose }) => {
  const [copied, setCopied] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom while streaming
  useEffect(() => {
    if (response.isStreaming && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [response.content, response.isStreaming]);

  const handleCopy = () => {
    navigator.clipboard.writeText(response.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      /* Enter: spring up from below the pill with a subtle scale bloom */
      initial={{ opacity: 0, y: 14, scale: 0.96 }}
      animate={{ opacity: 1, y: 0,  scale: 1 }}
      /* Exit: quick scale-down + fade toward the pill */
      exit={{
        opacity: 0,
        y: 10,
        scale: 0.96,
        transition: EXIT_EASE,
      }}
      transition={ENTER_SPRING}
      className="w-full mb-1.5 flex flex-col rounded-2xl overflow-hidden border border-zinc-800 bg-zinc-950 shadow-2xl shadow-black/80"
    >
      {/* Slim top subtle accent line */}
      <div className="h-px w-full bg-gradient-to-r from-transparent via-zinc-400/25 to-transparent" />

      {/* Header: Query Badge + Actions */}
      <div className="flex items-center justify-between px-3.5 pt-3 pb-2">
        {/* Left: Query Badge */}
        <div className="flex items-center gap-2 min-w-0 flex-1">
          {response.query && (
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-zinc-900 text-zinc-300 border border-zinc-800 max-w-full truncate shadow-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-400" />
              <span className="truncate">{response.query}</span>
            </div>
          )}
        </div>

        {/* Right: copy + close ghost action buttons */}
        <div className="flex items-center gap-1 shrink-0 ml-2">
          <button
            onMouseDown={(e) => e.stopPropagation()}
            onClick={handleCopy}
            className="w-7 h-7 flex items-center justify-center text-zinc-400 hover:text-zinc-100 rounded-md hover:bg-zinc-800/80 transition-colors border border-transparent hover:border-zinc-700/60 cursor-pointer"
            title="Copy response"
            type="button"
          >
            <AnimatePresence mode="wait">
              {copied ? (
                <motion.span key="check" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }} transition={{ duration: 0.12 }}>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                </motion.span>
              ) : (
                <motion.span key="copy" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }} transition={{ duration: 0.12 }}>
                  <Copy className="w-3.5 h-3.5" />
                </motion.span>
              )}
            </AnimatePresence>
          </button>

          {onClose && (
            <button
              onMouseDown={(e) => e.stopPropagation()}
              onClick={onClose}
              className="w-7 h-7 flex items-center justify-center text-zinc-400 hover:text-zinc-100 rounded-md hover:bg-zinc-800/80 transition-colors border border-transparent hover:border-zinc-700/60 cursor-pointer"
              title="Dismiss"
              type="button"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Divider */}
      <div className="mx-3.5 h-px bg-zinc-800/70" />

      {/* Scrollable response body */}
      <div
        ref={scrollRef}
        className="px-3.5 py-3 max-h-[170px] overflow-y-auto text-[13px] leading-relaxed text-zinc-200 font-normal tracking-tight select-text"
      >
        <span className="whitespace-pre-line">{response.content}</span>
        {response.isStreaming && (
          <span className="inline-block w-1.5 h-3.5 ml-1 bg-zinc-300 cursor-blink align-middle" />
        )}
      </div>
    </motion.div>
  );
};
