import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Square, Radio } from "lucide-react";
import { BackgroundWaveform } from "./BackgroundWaveform";
import type { AssistantState } from "../../types/assistant";
import { UI_MESSAGES } from "../../constants/messages";

interface FloatingPillProps {
  state: AssistantState;
  onToggleMic: () => void;
  liveTranscript?: string;
  connectionStatus?: "connected" | "connecting" | "disconnected";
  isFollowup?: boolean;
}

// Wave color + orb config per state in refined shadcn palette
const STATE_CONFIG = {
  listening: {
    waveColor: "rgba(250, 250, 250, 0.9)", // zinc-50 / white wave
    orbColor: "rgba(255, 255, 255, 0.18)",
    intensity: 0.8,
    label: null,
    textColor: "text-zinc-100",
  },
  thinking: {
    waveColor: "rgba(168, 85, 247, 0.9)", // violet-500
    orbColor: "rgba(147, 51, 234, 0.25)",
    intensity: 0.6,
    label: UI_MESSAGES.THINKING,
    textColor: "text-zinc-300",
  },
  speaking: {
    waveColor: "rgba(16, 185, 129, 0.9)", // emerald-500
    orbColor: "rgba(5, 150, 105, 0.25)",
    intensity: 0.9,
    label: null,
    textColor: "text-emerald-400",
  },
};

export const FloatingPill: React.FC<FloatingPillProps> = ({
  state,
  onToggleMic,
  liveTranscript,
  connectionStatus = "disconnected",
  isFollowup = false,
}) => {
  const isListening = state === "listening";
  const isThinking = state === "thinking";
  const isSpeaking = state === "speaking";
  const isActive = isListening || isThinking || isSpeaking;

  const cfg = isListening
    ? STATE_CONFIG.listening
    : isThinking
      ? STATE_CONFIG.thinking
      : isSpeaking
        ? STATE_CONFIG.speaking
        : null;

  // Mic button styling per shadcn state
  const micBg = isListening
    ? "bg-zinc-100 text-zinc-950 border-white shadow-[0_0_20px_rgba(255,255,255,0.35)]"
    : isThinking
      ? "bg-violet-600 text-white border-violet-400/40 shadow-[0_0_16px_rgba(139,92,246,0.35)]"
      : isSpeaking
        ? "bg-emerald-600 text-white border-emerald-400/40 shadow-[0_0_16px_rgba(16,185,129,0.35)]"
        : "bg-zinc-900/90 hover:bg-zinc-800 text-zinc-200 border-zinc-700/70 hover:border-zinc-500/80 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)]";

  return (
    <motion.div
      layout
      className={`relative w-full flex items-center justify-between px-3.5 py-2.5 rounded-full border shadow-2xl shadow-black/80 select-none overflow-hidden transition-all duration-300 ${
        isActive
          ? "bg-zinc-950 border-zinc-700/80"
          : "bg-zinc-950 border-zinc-800 hover:border-zinc-700/60"
      }`}
    >
      {/* ── Background waveform layer (behind everything) ──────────────────── */}
      <AnimatePresence>
        {cfg && (
          <motion.div
            key={`wave-${state}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5, ease: "easeInOut" }}
            style={{
              position: "absolute",
              inset: 0,
              zIndex: 0,
              borderRadius: "9999px",
              overflow: "hidden",
            }}
          >
            <BackgroundWaveform
              color={cfg.waveColor}
              intensity={cfg.intensity}
              layers={3}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Bottom-center radial orb glow ─────────────────────────────────── */}
      <AnimatePresence>
        {cfg && (
          <motion.div
            key={`orb-${state}`}
            aria-hidden="true"
            initial={{ opacity: 0, scale: 0.6, y: 20 }}
            animate={{
              opacity: [0.7, 1, 0.75],
              scale: [1, 1.2, 1],
              y: [8, 2, 8],
              x: [0, 5, -4, 0],
            }}
            exit={{ opacity: 0, scale: 0.5, y: 20 }}
            transition={{
              opacity: { duration: 0.4, ease: "easeOut" },
              scale: { duration: 3.5, repeat: Infinity, ease: "easeInOut" },
              y: { duration: 3.5, repeat: Infinity, ease: "easeInOut" },
              x: { duration: 5, repeat: Infinity, ease: "easeInOut" },
            }}
            style={{
              position: "absolute",
              bottom: "-28px",
              left: "50%",
              transform: "translateX(-50%)",
              width: "220px",
              height: "80px",
              background: `radial-gradient(ellipse at 50% 100%, ${cfg.orbColor} 0%, transparent 72%)`,
              filter: "blur(1px)",
              pointerEvents: "none",
              zIndex: 0,
            }}
          />
        )}
      </AnimatePresence>

      {/* ── Top edge glow line ────────────────────────────────────────────── */}
      <AnimatePresence>
        {isActive && (
          <motion.div
            key="glow-line"
            initial={{ opacity: 0, scaleX: 0 }}
            animate={{ opacity: 1, scaleX: 1 }}
            exit={{ opacity: 0, scaleX: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className={`absolute inset-x-8 top-0 h-px rounded-full pointer-events-none ${
              isListening
                ? "bg-gradient-to-r from-transparent via-white/50 to-transparent"
                : isThinking
                  ? "bg-gradient-to-r from-transparent via-violet-400/50 to-transparent"
                  : "bg-gradient-to-r from-transparent via-emerald-400/50 to-transparent"
            }`}
          />
        )}
      </AnimatePresence>

      {/* ── Content sits above wave (z-10) ────────────────────────────────── */}

      {/* Left: connection status */}
      <div className="relative z-10 flex items-center">
        <div className="relative w-7 h-7 flex items-center justify-center">
          <Radio
            color={
              connectionStatus === "connected"
                ? "green"
                : connectionStatus === "connecting"
                  ? "yellow"
                  : "gray"
            }
            className={`w-3.5 h-3.5 transition-colors duration-300 ${
              connectionStatus === "connected"
                ? "text-zinc-400"
                : connectionStatus === "connecting"
                  ? "text-amber-400"
                  : "text-zinc-600"
            }`}
          />
        </div>
      </div>

      {/* Center: state label */}
      <div className="relative z-10 flex-1 mx-2 flex items-center justify-center overflow-hidden min-w-0">
        <AnimatePresence mode="wait">
          {isListening ? (
            <motion.div
              key="listening"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.16 }}
              className="flex items-center gap-2 max-w-full min-w-0"
            >
              {liveTranscript ? (
                <span className="text-[12px] text-zinc-100 truncate font-normal tracking-tight">
                  "{liveTranscript}"
                </span>
              ) : (
                <motion.span
                  animate={{ opacity: [0.6, 1, 0.6] }}
                  transition={{
                    duration: 1.8,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                  className="text-[12px] text-zinc-200 font-medium tracking-tight"
                >
                  {isFollowup
                    ? UI_MESSAGES.LISTENING_FOLLOWUP
                    : UI_MESSAGES.LISTENING}
                </motion.span>
              )}
            </motion.div>
          ) : isThinking ? (
            <motion.div
              key="thinking"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.16 }}
              className="flex items-center gap-1.5"
            >
              <span className="text-[12px] text-zinc-300 font-medium tracking-tight">
                {UI_MESSAGES.THINKING}
              </span>
              <span className="inline-flex gap-1 items-center">
                <span className="w-1 h-1 rounded-full bg-violet-400 dot-bounce-1" />
                <span className="w-1 h-1 rounded-full bg-violet-400 dot-bounce-2" />
                <span className="w-1 h-1 rounded-full bg-violet-400 dot-bounce-3" />
              </span>
            </motion.div>
          ) : isSpeaking ? (
            <motion.div
              key="speaking"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.16 }}
            >
              <motion.span
                animate={{ opacity: [0.7, 1, 0.7] }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
                className="text-[12px] text-emerald-400 font-medium tracking-tight"
              >
                {UI_MESSAGES.SPEAKING}
              </motion.span>
            </motion.div>
          ) : (
            <motion.span
              key="idle"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.16 }}
              className="text-[12px] text-zinc-400 tracking-tight font-normal"
            >
              {connectionStatus === "connected"
                ? UI_MESSAGES.IDLE_PROMPT
                : UI_MESSAGES.WAITING_FOR_BACKEND}
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Right: mic button */}
      <motion.button
        className={`relative z-10 w-9 h-9 rounded-full flex items-center justify-center cursor-pointer transition-all duration-200 border ${micBg} ${
          isListening ? "mic-glow" : ""
        }`}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.94 }}
        onMouseDown={(e) => e.stopPropagation()}
        onClick={onToggleMic}
        title={isActive ? UI_MESSAGES.MIC_STOP : UI_MESSAGES.MIC_START}
        type="button"
      >
        <AnimatePresence mode="wait">
          {isActive ? (
            <motion.span
              key="stop"
              initial={{ scale: 0, rotate: -90 }}
              animate={{ scale: 1, rotate: 0 }}
              exit={{ scale: 0, rotate: 90 }}
              transition={{ duration: 0.16 }}
            >
              <Square className="w-3.5 h-3.5 fill-current" />
            </motion.span>
          ) : (
            <motion.span
              key="mic"
              initial={{ scale: 0, rotate: 90 }}
              animate={{ scale: 1, rotate: 0 }}
              exit={{ scale: 0, rotate: -90 }}
              transition={{ duration: 0.16 }}
            >
              <Mic style={{ width: 18, height: 18 }} />
            </motion.span>
          )}
        </AnimatePresence>
      </motion.button>
    </motion.div>
  );
};
