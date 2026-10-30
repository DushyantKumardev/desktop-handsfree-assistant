import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Plus } from "lucide-react";
import { GeminiWaveform } from "./GeminiWaveform";
import { DragHandle } from "./DragHandle";
import type { AssistantState } from "../../types/assistant";

interface FloatingPillProps {
  state: AssistantState;
  onToggleMic: () => void;
  liveTranscript?: string;
  connectionStatus?: "connected" | "connecting" | "disconnected";
  isFollowup?: boolean;
  statusMessage?: string;
  onDragStart?: (e: React.MouseEvent) => void;
}

export const FloatingPill: React.FC<FloatingPillProps> = ({
  state,
  onToggleMic,
  liveTranscript,
  statusMessage,
  onDragStart,
}) => {
  const isListening = state === "listening";
  const isThinking = state === "thinking";
  const isSpeaking = state === "speaking";
  const isBusy = isThinking || isSpeaking;

  const currentStatusText =
    statusMessage || (isSpeaking ? "Speaking..." : "Just a sec...");

  return (
    <motion.div
      layout
      transition={{ layout: { type: "spring", stiffness: 420, damping: 34 } }}
      className="relative w-full flex flex-col items-center justify-between px-3.5 pt-1 pb-2.5 rounded-full bg-surface-pill border border-border-subtle shadow-[0_12px_36px_rgba(0,0,0,0.75)] select-none overflow-hidden transition-colors duration-300"
    >
      <DragHandle onDragStart={onDragStart} className="pt-1 pb-1" />

      <AnimatePresence>
        {(isThinking || isSpeaking || isListening) && (
          <motion.div
            key="ambient-glow"
            initial={{ opacity: 0, scaleY: 0.4 }}
            animate={{
              opacity: isThinking ? [0.6, 0.95, 0.6] : 0.5,
              scaleY: isThinking ? [1, 1.18, 1] : 1,
            }}
            exit={{ opacity: 0, scaleY: 0.4, transition: { duration: 0.25 } }}
            transition={{
              duration: 2.2,
              repeat: isThinking ? Infinity : 0,
              ease: "easeInOut",
            }}
            className="absolute inset-x-0 bottom-0 h-10 pointer-events-none rounded-b-full"
            style={{
              background: "var(--glow-gradient)",
              zIndex: 0,
            }}
          />
        )}
      </AnimatePresence>

      <div className="relative z-10 w-full flex items-center justify-between h-11 px-1">
        {/* Left Section: Smooth status crossfade */}
        <div className="flex items-center gap-2.5 min-w-0">
          <AnimatePresence mode="popLayout" initial={false}>
            {isBusy ? (
              <motion.div
                key="busy-status-badge"
                layout
                initial={{ opacity: 0, x: -10, filter: "blur(4px)" }}
                animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
                exit={{ opacity: 0, x: -8, filter: "blur(4px)" }}
                transition={{ duration: 0.22, ease: "easeOut" }}
                className="flex items-center gap-2 pl-1"
              >
                <motion.span
                  animate={{ scale: [1, 1.25, 1], opacity: [0.6, 1, 0.6] }}
                  transition={{
                    duration: 1.4,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                  className="w-2 h-2 rounded-full bg-accent-hover shrink-0"
                />
                <span className="text-[15px] text-content-primary font-normal tracking-tight font-sans truncate max-w-[210px]">
                  {currentStatusText}
                </span>
              </motion.div>
            ) : (
              <motion.div
                key="idle-plus-group"
                layout
                initial={{ opacity: 0, x: -8, filter: "blur(4px)" }}
                animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
                exit={{ opacity: 0, x: -8, filter: "blur(4px)" }}
                transition={{ duration: 0.22, ease: "easeOut" }}
                className="flex items-center gap-2.5"
              >
                <button
                  type="button"
                  className="w-7 h-7 flex items-center justify-center text-content-secondary hover:text-white rounded-full transition-colors cursor-pointer"
                  title="Action"
                  onClick={onToggleMic}
                >
                  <Plus className="w-5 h-5 stroke-[2]" />
                </button>

                <AnimatePresence>
                  {state === "idle" && (
                    <motion.span
                      layout
                      initial={{ opacity: 0, x: -6, width: 0 }}
                      animate={{ opacity: 1, x: 0, width: "auto" }}
                      exit={{ opacity: 0, x: -6, width: 0 }}
                      transition={{ duration: 0.2 }}
                      className="text-[15px] text-content-secondary font-normal tracking-tight font-sans whitespace-nowrap overflow-hidden"
                    >
                      Ask Assistant
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Center: Live Audio Waveform or Transcript */}
        <AnimatePresence>
          {isListening && (
            <motion.div
              layout
              initial={{ opacity: 0, scale: 0.9, filter: "blur(4px)" }}
              animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
              exit={{ opacity: 0, scale: 0.92, filter: "blur(3px)" }}
              transition={{ duration: 0.2, ease: "easeOut" }}
              className="flex-1 flex items-center justify-center px-2 min-w-0"
            >
              <AnimatePresence mode="popLayout" initial={false}>
                {liveTranscript ? (
                  <motion.span
                    key="live-transcript"
                    layout
                    initial={{ opacity: 0, y: 4, filter: "blur(2px)" }}
                    animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                    exit={{ opacity: 0, y: -4, filter: "blur(2px)" }}
                    transition={{ duration: 0.18 }}
                    className="text-[14px] text-content-primary font-normal truncate max-w-[220px]"
                  >
                    "{liveTranscript}"
                  </motion.span>
                ) : (
                  <motion.div
                    key="waveform"
                    layout
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ duration: 0.18 }}
                  >
                    <GeminiWaveform barCount={15} />
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Right Section: Action Button & Smooth Wave Indicators */}
        <div className="flex items-center gap-2.5 shrink-0">
          <motion.button
            layout
            whileTap={{ scale: 0.92 }}
            type="button"
            onClick={onToggleMic}
            className={`w-10 h-10 rounded-full flex items-center justify-center shadow-md cursor-pointer transition-colors duration-300 ${
              isListening
                ? "bg-accent hover:bg-accent-hover text-accent-fg shadow-[var(--glow-shadow)]"
                : isBusy
                  ? "bg-accent hover:bg-accent-hover text-accent-fg"
                  : "bg-accent-dark hover:bg-accent-dark-hover text-accent-fg"
            }`}
            title={
              isBusy
                ? "Cancel"
                : isListening
                  ? "Stop listening"
                  : "Start listening"
            }
          >
            <AnimatePresence mode="popLayout" initial={false}>
              {isBusy ? (
                <motion.div
                  key="square"
                  initial={{ scale: 0.6, opacity: 0, rotate: -25 }}
                  animate={{ scale: 1, opacity: 1, rotate: 0 }}
                  exit={{ scale: 0.6, opacity: 0, rotate: 25 }}
                  transition={{ duration: 0.16, ease: "easeOut" }}
                  className="flex items-center justify-center"
                >
                  <svg
                    className="w-4 h-4 text-white"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <rect x="4.5" y="4.5" width="15" height="15" rx="4" />
                  </svg>
                </motion.div>
              ) : (
                <motion.div
                  key="mic"
                  initial={{ scale: 0.6, opacity: 0, rotate: 25 }}
                  animate={{ scale: 1, opacity: 1, rotate: 0 }}
                  exit={{ scale: 0.6, opacity: 0, rotate: -25 }}
                  transition={{ duration: 0.16, ease: "easeOut" }}
                  className="flex items-center justify-center"
                >
                  <Mic className="w-5 h-5 stroke-[2.2]" />
                </motion.div>
              )}
            </AnimatePresence>
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
};
