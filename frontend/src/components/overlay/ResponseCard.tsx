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
      initial={{ opacity: 0, y: 18, scale: 0.94, filter: "blur(6px)" }}
      animate={{ opacity: 1, y: 0,  scale: 1,    filter: "blur(0px)" }}
      /* Exit: quick scale-down + fade toward the pill */
      exit={{
        opacity: 0,
        y: 10,
        scale: 0.95,
        filter: "blur(4px)",
        transition: EXIT_EASE,
      }}
      transition={ENTER_SPRING}
      className="w-full mb-1.5 flex flex-col rounded-[18px] overflow-hidden border border-white/[0.09] shadow-[0_20px_50px_rgba(0,0,0,0.7)] backdrop-blur-2xl"
      style={{ background: "linear-gradient(160deg, #1E1C1A 0%, #18160F 100%)", willChange: "transform, opacity, filter" }}
    >
      {/* Slim top accent line */}
      <div className="h-px w-full bg-gradient-to-r from-transparent via-amber-500/40 to-transparent" />

      {/* Header: just query + streaming dot + close */}
      <div className="flex items-center justify-between px-3.5 pt-2.5 pb-1.5">
        {/* Left: query only */}
        <div className="flex items-center gap-2 min-w-0 flex-1">
          {/* Query echo — truncated, italic, subtle */}
          {response.query && (
            <p className="text-[11px] text-white/40 italic font-light truncate min-w-0">
              {response.query}
            </p>
          )}
        </div>

        {/* Right: copy + close only */}
        <div className="flex items-center gap-0.5 shrink-0 ml-2">
          <button
            onMouseDown={(e) => e.stopPropagation()}
            onClick={handleCopy}
            className="w-6 h-6 flex items-center justify-center text-white/25 hover:text-white/60 rounded-lg hover:bg-white/8 transition-colors cursor-pointer"
            title="Copy"
            type="button"
          >
            <AnimatePresence mode="wait">
              {copied ? (
                <motion.span key="check" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }} transition={{ duration: 0.13 }}>
                  <Check className="w-3 h-3 text-emerald-400" />
                </motion.span>
              ) : (
                <motion.span key="copy" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }} transition={{ duration: 0.13 }}>
                  <Copy className="w-3 h-3" />
                </motion.span>
              )}
            </AnimatePresence>
          </button>

          {onClose && (
            <button
              onMouseDown={(e) => e.stopPropagation()}
              onClick={onClose}
              className="w-6 h-6 flex items-center justify-center text-white/25 hover:text-white/60 rounded-lg hover:bg-white/8 transition-colors cursor-pointer"
              title="Dismiss"
              type="button"
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Divider */}
      <div className="mx-3.5 h-px bg-white/[0.06]" />

      {/* Scrollable response body */}
      <div
        ref={scrollRef}
        className="px-3.5 py-2.5 max-h-[160px] overflow-y-auto text-[13px] leading-[1.72] text-slate-100/88 font-light tracking-wide select-text"
      >
        <span className="whitespace-pre-line">{response.content}</span>
      </div>
    </motion.div>
  );
};
