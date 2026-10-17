import { useState, useEffect, useRef, useCallback } from "react";
import { AnimatePresence } from "framer-motion";
import { FloatingPill } from "./components/overlay/FloatingPill";
import { ResponseCard } from "./components/overlay/ResponseCard";
import {
  initDesktopRuntime,
  setWindowSize,
  handleWindowDrag,
  showWindow,
} from "./services/desktop";
import {
  AssistantWebSocketClient,
  type ConnectionStatus,
} from "./services/websocket";
import type { AssistantState, AssistantResponse, WSMessage } from "./types/assistant";

export default function App() {
  const [state, setState] = useState<AssistantState>("idle");
  const [response, setResponse] = useState<AssistantResponse | null>(null);
  const [liveTranscript, setLiveTranscript] = useState<string>("");
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("disconnected");
  const [isFollowup, setIsFollowup] = useState<boolean>(false);

  const wsClientRef = useRef<AssistantWebSocketClient | null>(null);
  const currentQueryRef = useRef<string>("");

  // Initialize Desktop Native Environment
  useEffect(() => {
    initDesktopRuntime(() => {
      setWindowSize(440, 85);
      // Auto-hide on blur is disabled — window stays visible when unfocused
    });
  }, []);

  // Initialize and maintain WebSocket connection to Python backend
  useEffect(() => {
    const handleWSMessage = (msg: WSMessage) => {
      console.log("[WS] Received message:", msg.type, msg.payload);

      switch (msg.type) {
        case "SERVER_SHOW_WIDGET":
          showWindow();
          break;

        case "SERVER_STATE_CHANGE": {
          const payload = msg.payload as { state?: AssistantState; is_followup?: boolean };
          if (payload?.state) {
            setState(payload.state);
            const followup = !!payload.is_followup;
            setIsFollowup(followup);
            if (payload.state === "listening") {
              setLiveTranscript("");
              if (!followup) {
                setResponse(null);
              }
            } else if (payload.state === "idle") {
              setLiveTranscript("");
              setIsFollowup(false);
            }
          }
          break;
        }

        case "SERVER_TRANSCRIPTION": {
          const payload = msg.payload as { text?: string };
          if (payload?.text) {
            setLiveTranscript(payload.text);
            currentQueryRef.current = payload.text;
          }
          break;
        }

        case "SERVER_STREAM_CHUNK": {
          const payload = msg.payload as { chunk?: string; query?: string };
          if (payload?.chunk) {
            const queryText = payload.query || currentQueryRef.current || "Voice Request";
            setResponse((prev) => {
              if (!prev) {
                return {
                  id: Date.now().toString(),
                  query: queryText,
                  content: payload.chunk || "",
                  isStreaming: true,
                  timestamp: "Just now",
                };
              }
              return {
                ...prev,
                query: prev.query || queryText,
                content: prev.content ? `${prev.content} ${payload.chunk}` : (payload.chunk || ""),
                isStreaming: true,
              };
            });
          }
          break;
        }

        case "SERVER_RESPONSE_COMPLETE": {
          const payload = msg.payload as { query?: string; content?: string; needs_followup?: boolean };
          setResponse((prev) => ({
            id: prev?.id || Date.now().toString(),
            query: payload?.query || prev?.query || currentQueryRef.current || "Voice Request",
            content: payload?.content || prev?.content || "",
            isStreaming: false,
            timestamp: "Just now",
          }));
          if (!payload?.needs_followup) {
            setState("idle");
          }
          setLiveTranscript("");
          break;
        }

        case "SERVER_ERROR": {
          const payload = msg.payload as { error?: string };
          console.error("[WS] Server error:", payload?.error);
          setState("idle");
          setIsFollowup(false);
          break;
        }

        default:
          break;
      }
    };

    const client = new AssistantWebSocketClient(
      "ws://127.0.0.1:8765",
      handleWSMessage,
      (status) => setConnectionStatus(status)
    );

    wsClientRef.current = client;
    client.connect();

    return () => {
      client.disconnect();
    };
  }, []);

  // Dynamically resize native window when response card expands
  useEffect(() => {
    if (response) {
      setWindowSize(440, 380);
    } else {
      setWindowSize(440, 85);
    }
  }, [response]);

  const cancelWorkflow = useCallback(() => {
    if (wsClientRef.current?.isConnected()) {
      wsClientRef.current.send("CLIENT_CANCEL");
    }
    setState("idle");
    setIsFollowup(false);
    setLiveTranscript("");
  }, []);

  const handleToggleMic = () => {
    // If assistant is currently active, cancel current turn
    if (state !== "idle") {
      cancelWorkflow();
      return;
    }

    // Trigger backend listening via WebSocket
    if (wsClientRef.current?.isConnected()) {
      wsClientRef.current.send("CLIENT_TRIGGER_LISTEN");
      setState("listening");
      setIsFollowup(false);
      setResponse(null);
      setLiveTranscript("");
    } else {
      // If offline, attempt reconnecting
      wsClientRef.current?.connect();
    }
  };

  return (
    <div
      id="window-drag-region"
      onMouseDown={handleWindowDrag}
      className="w-full h-full flex flex-col justify-end items-center px-2 pb-2 bg-transparent select-none cursor-grab active:cursor-grabbing"
    >
      <div className="w-full flex flex-col items-center justify-end gap-1.5">
        {/* Streaming Response Card */}
        <AnimatePresence mode="sync">
          {response && (
            <ResponseCard
              response={response}
              onClose={() => setResponse(null)}
            />
          )}
        </AnimatePresence>

        {/* Main Floating Voice Pill Bar */}
        <FloatingPill
          state={state}
          onToggleMic={handleToggleMic}
          liveTranscript={liveTranscript}
          connectionStatus={connectionStatus}
          isFollowup={isFollowup}
        />
      </div>
    </div>
  );
}
