/**
 * Central UI messages, status texts, and labels for the frontend overlay.
 */

export const UI_MESSAGES = {
  // Connection states
  CONNECTED: "Backend connected",
  CONNECTING: "Connecting…",
  OFFLINE: "Backend offline",
  WAITING_FOR_BACKEND: "Waiting for backend…",

  // Assistant states
  IDLE_PROMPT: "Say the wake word or tap mic",
  LISTENING: "Listening…",
  LISTENING_FOLLOWUP: "Listening for reply…",
  THINKING: "Just a sec…",
  SPEAKING: "Speaking…",

  // Controls & Tooltips
  MIC_START: "Start voice input",
  MIC_STOP: "Stop",

  // Fallback labels
  DEFAULT_QUERY_TITLE: "Voice Request",
  DEFAULT_NOTIFICATION_TITLE: "Assistant Alert",
  JUST_NOW: "Just now",
} as const;
