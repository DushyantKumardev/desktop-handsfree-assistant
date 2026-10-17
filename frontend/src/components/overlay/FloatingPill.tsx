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

// Wave color + orb config per state
const STATE_CONFIG = {
  listening: {
    waveColor:  "rgba(251, 146, 60, 1)",   // amber-400
    orbColor:   "rgba(194, 98, 0, 0.50)",
    intensity:  0.9,
    label:      null,
    textColor:  "text-amber-200/80",
  },
  thinking: {
    waveColor:  "rgba(167, 139, 250, 1)",  // violet-400
    orbColor:   "rgba(124, 77, 255, 0.40)",
    intensity:  0.6,
    label:      UI_MESSAGES.THINKING,
    textColor:  "text-white/60",
  },
  speaking: {
    waveColor:  "rgba(52, 211, 153, 1)",   // emerald-400
    orbColor:   "rgba(5, 150, 105, 0.35)",
    intensity:  1.0,
    label:      null,
    textColor:  "text-emerald-200/80",
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
  const isThinking  = state === "thinking";
  const isSpeaking  = state === "speaking";
  const isActive    = isListening || isThinking || isSpeaking;

  const cfg = isListening
    ? STATE_CONFIG.listening
    : isThinking
    ? STATE_CONFIG.thinking
    : isSpeaking
    ? STATE_CONFIG.speaking
    : null;

  // Mic button gradient shifts per state
  const micBg = isListening
    ? "bg-gradient-to-br from-[#E06B00] to-[#B84E00]"
    : isThinking
    ? "bg-gradient-to-br from-[#7C4DFF] to-[#5B37C5]"
    : isSpeaking
    ? "bg-gradient-to-br from-[#059669] to-[#047857]"
    : "bg-gradient-to-br from-[#C26200] to-[#943F00]";

  return (
    <motion.div
      layout
      className={`relative w-full flex items-center justify-between px-3 py-2 rounded-full border shadow-[0_16px_48px_rgba(0,0,0,0.7)] backdrop-blur-2xl select-none overflow-hidden transition-colors duration-500 ${
        isActive
          ? "bg-[#1C1A18]/98 border-white/[0.14]"
          : "bg-[#1E1C1A]/95 border-white/[0.09]"
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
            style={{ position: "absolute", inset: 0, zIndex: 0, borderRadius: "9999px", overflow: "hidden" }}
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
              scale:   [1, 1.2, 1],
              y:       [8, 2, 8],
              x:       [0, 5, -4, 0],
            }}
            exit={{ opacity: 0, scale: 0.5, y: 20 }}
            transition={{
              opacity: { duration: 0.4, ease: "easeOut" },
              scale:   { duration: 3.5, repeat: Infinity, ease: "easeInOut" },
              y:       { duration: 3.5, repeat: Infinity, ease: "easeInOut" },
              x:       { duration: 5,   repeat: Infinity, ease: "easeInOut" },
            }}
            style={{
              position:  "absolute",
              bottom:    "-28px",
              left:      "50%",
              transform: "translateX(-50%)",
              width:     "220px",
              height:    "80px",
              background:`radial-gradient(ellipse at 50% 100%, ${cfg.orbColor} 0%, transparent 72%)`,
              filter:    "blur(1px)",
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
                ? "bg-gradient-to-r from-transparent via-amber-400/55 to-transparent"
                : isThinking
                ? "bg-gradient-to-r from-transparent via-violet-400/55 to-transparent"
                : "bg-gradient-to-r from-transparent via-emerald-400/55 to-transparent"
            }`}
          />
        )}
      </AnimatePresence>

      {/* ── Content sits above wave (z-10) ────────────────────────────────── */}

      {/* Left: connection status */}
      <div className="relative z-10 flex items-center">
        <div className="relative w-7 h-7 flex items-center justify-center">
          <Radio
            className={`w-3.5 h-3.5 transition-colors duration-500 ${
              connectionStatus === "connected"
                ? "text-emerald-400"
                : connectionStatus === "connecting"
                ? "text-amber-400"
                : "text-white/20"
            }`}
          />
          <span
            className={`absolute bottom-0.5 right-0.5 w-1.5 h-1.5 rounded-full ${
              connectionStatus === "connected"
                ? "bg-emerald-500 orb-pulse shadow-[0_0_6px_rgba(16,185,129,0.8)]"
                : connectionStatus === "connecting"
                ? "bg-amber-400 animate-pulse"
                : "bg-white/15"
            }`}
            title={
              connectionStatus === "connected"
                ? UI_MESSAGES.CONNECTED
                : connectionStatus === "connecting"
                ? UI_MESSAGES.CONNECTING
                : UI_MESSAGES.OFFLINE
            }
          />
        </div>
      </div>

      {/* Center: state label */}
      <div className="relative z-10 flex-1 mx-2 flex items-center justify-center overflow-hidden min-w-0">
        <AnimatePresence mode="wait">
          {isListening ? (
            <motion.div
              key="listening"
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{ duration: 0.18 }}
              className="flex items-center gap-2 max-w-full min-w-0"
            >
              {liveTranscript ? (
                <span className="text-[11px] text-amber-100/90 truncate italic font-light tracking-wide drop-shadow-sm">
                  {liveTranscript}
                </span>
              ) : (
                <motion.span
                  animate={{ opacity: [0.45, 0.9, 0.45] }}
                  transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
                  className="text-[12px] text-amber-200/70 font-light tracking-wide"
                >
                  {isFollowup ? UI_MESSAGES.LISTENING_FOLLOWUP : UI_MESSAGES.LISTENING}
                </motion.span>
              )}
            </motion.div>
          ) : isThinking ? (
            <motion.div
              key="thinking"
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{ duration: 0.18 }}
            >
              <motion.span
                animate={{ opacity: [0.45, 0.95, 0.45] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                className="text-[12px] text-white/65 font-light tracking-wide"
              >
                {UI_MESSAGES.THINKING}
              </motion.span>
            </motion.div>
          ) : isSpeaking ? (
            <motion.div
              key="speaking"
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{ duration: 0.18 }}
            >
              <motion.span
                animate={{ opacity: [0.55, 1, 0.55] }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                className="text-[12px] text-emerald-200/80 font-light tracking-wide"
              >
                {UI_MESSAGES.SPEAKING}
              </motion.span>
            </motion.div>
          ) : (
            <motion.span
              key="idle"
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{ duration: 0.18 }}
              className="text-[12px] text-white/28 tracking-wide font-light"
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
        className={`relative z-10 w-10 h-10 rounded-full flex items-center justify-center text-white shadow-lg cursor-pointer transition-all duration-300 ${micBg} ${
          isListening ? "mic-glow" : ""
        }`}
        whileHover={{ scale: 1.07 }}
        whileTap={{ scale: 0.92 }}
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
