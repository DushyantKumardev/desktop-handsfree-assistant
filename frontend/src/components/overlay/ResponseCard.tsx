import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Copy, Check, X } from "lucide-react";
import { DragHandle } from "./DragHandle";
import type { AssistantResponse } from "../../types/assistant";

const ENTER_SPRING = {
  type: "spring",
  stiffness: 380,
  damping: 32,
  mass: 0.9,
} as const;

const EXIT_EASE = { duration: 0.2, ease: [0.4, 0, 1, 1] } as const;

interface ResponseCardProps {
  response: AssistantResponse;
  onClose?: () => void;
  onDragStart?: (e: React.MouseEvent) => void;
}

export const ResponseCard: React.FC<ResponseCardProps> = ({
  response,
  onClose,
  onDragStart,
}) => {
  const [copied, setCopied] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

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
      initial={{ opacity: 0, y: 14, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 10, scale: 0.96, transition: EXIT_EASE }}
      transition={ENTER_SPRING}
      className="w-full mb-2 flex flex-col rounded-[26px] overflow-hidden bg-surface-card border border-border-subtle shadow-[0_16px_48px_rgba(0,0,0,0.85)] select-none"
    >
      <DragHandle onDragStart={onDragStart} className="pt-2 pb-1.5" />

      <div
        ref={scrollRef}
        className="px-5 pt-2 pb-3 max-h-[190px] overflow-y-auto text-[15px] leading-relaxed text-content-primary font-normal tracking-tight select-text font-sans"
      >
        <span className="whitespace-pre-line">{response.content}</span>
        {response.isStreaming && (
          <span className="inline-block w-1.5 h-4 ml-1 bg-accent-hover cursor-blink align-middle rounded-full" />
        )}

        <div className="mt-3 text-[12px] text-content-muted font-normal select-none">
          Assistant is AI and can make mistakes.
        </div>
      </div>

      <div className="flex items-center justify-between px-4 py-2.5 border-t border-border-subtle/60 bg-surface-subtle/60">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleCopy}
            className="w-7 h-7 flex items-center justify-center text-content-muted hover:text-content-primary rounded-full transition-colors cursor-pointer"
            title="Copy response"
          >
            <AnimatePresence mode="wait">
              {copied ? (
                <motion.span
                  key="check"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                >
                  <Check className="w-4 h-4 text-emerald-400 stroke-[2]" />
                </motion.span>
              ) : (
                <motion.span
                  key="copy"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                >
                  <Copy className="w-4 h-4 stroke-[1.8]" />
                </motion.span>
              )}
            </AnimatePresence>
          </button>
        </div>

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center text-content-muted hover:text-white rounded-full transition-colors cursor-pointer"
            title="Dismiss"
          >
            <X className="w-4 h-4 stroke-[2]" />
          </button>
        )}
      </div>
    </motion.div>
  );
};
