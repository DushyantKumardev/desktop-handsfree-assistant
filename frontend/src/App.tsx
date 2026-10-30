import { useState, useEffect, useRef, useCallback } from "react";
import { AnimatePresence } from "framer-motion";
import { FloatingPill } from "./components/overlay/FloatingPill";
import { ResponseCard } from "./components/overlay/ResponseCard";
import {
  initDesktopRuntime,
  setWindowSize,
  handleWindowDrag,
  showWindow,
  showNativeNotification,
  ensureAlwaysOnTop,
} from "./services/desktop";
import {
  AssistantWebSocketClient,
  type ConnectionStatus,
} from "./services/websocket";
import type {
  AssistantState,
  AssistantResponse,
  WSMessage,
} from "./types/assistant";
import { UI_MESSAGES } from "./constants/messages";

export default function App() {
  const [state, setState] = useState<AssistantState>("idle");
  const [response, setResponse] = useState<AssistantResponse | null>(null);
  const [liveTranscript, setLiveTranscript] = useState<string>("");
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("disconnected");
  const [isFollowup, setIsFollowup] = useState<boolean>(false);

  const wsClientRef = useRef<AssistantWebSocketClient | null>(null);
  const currentQueryRef = useRef<string>("");

  // Initialize Desktop Native Environment
  useEffect(() => {
    initDesktopRuntime(() => {
      setWindowSize(440, 100);
      ensureAlwaysOnTop();
    });

    const handleBlur = () => {
      ensureAlwaysOnTop();
    };
    window.addEventListener("blur", handleBlur);
    return () => {
      window.removeEventListener("blur", handleBlur);
    };
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
          const payload = msg.payload as {
            state?: AssistantState;
            is_followup?: boolean;
          };
          if (payload?.state) {
            setState(payload.state);
            const followup = !!payload.is_followup;
            setIsFollowup(followup);
            if (payload.state === "listening") {
              setLiveTranscript("");
              setStatusMessage("");
            } else if (payload.state === "idle") {
              setLiveTranscript("");
              setStatusMessage("");
              setIsFollowup(false);
            }
          }
          break;
        }

        case "SERVER_STATUS": {
          const payload = msg.payload as { message?: string };
          if (payload?.message) {
            setStatusMessage(payload.message);
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
            const queryText =
              payload.query ||
              currentQueryRef.current ||
              UI_MESSAGES.DEFAULT_QUERY_TITLE;
            setResponse((prev) => {
              // Immediately start fresh if starting a new speech turn
              const isNewResponse =
                !prev ||
                !prev.isStreaming ||
                (payload.query && prev.query !== payload.query);

              if (isNewResponse) {
                return {
                  id: Date.now().toString(),
                  query: queryText,
                  content: payload.chunk || "",
                  isStreaming: true,
                  timestamp: UI_MESSAGES.JUST_NOW,
                };
              }

              return {
                ...prev,
                query: prev.query || queryText,
                content: prev.content
                  ? `${prev.content} ${payload.chunk}`
                  : payload.chunk || "",
                isStreaming: true,
              };
            });
          }
          break;
        }

        case "SERVER_RESPONSE_COMPLETE": {
          const payload = msg.payload as {
            query?: string;
            content?: string;
            needs_followup?: boolean;
          };
          setResponse((prev) => ({
            id: prev?.id || Date.now().toString(),
            query:
              payload?.query ||
              prev?.query ||
              currentQueryRef.current ||
              UI_MESSAGES.DEFAULT_QUERY_TITLE,
            content: payload?.content || prev?.content || "",
            isStreaming: false,
            timestamp: UI_MESSAGES.JUST_NOW,
          }));
          if (!payload?.needs_followup) {
            setState("idle");
          }
          setLiveTranscript("");
          setStatusMessage("");
          break;
        }

        case "SERVER_NOTIFICATION": {
          const payload = msg.payload as {
            title?: string;
            message?: string;
            taskId?: string;
          };
          const title =
            payload?.title || UI_MESSAGES.DEFAULT_NOTIFICATION_TITLE;
          const body = payload?.message || "";
          showNativeNotification(title, body);
          showWindow();
          setResponse({
            id: Date.now().toString(),
            query: title,
            content: body,
            isStreaming: false,
            timestamp: UI_MESSAGES.JUST_NOW,
          });
          break;
        }

        case "SERVER_ERROR": {
          const payload = msg.payload as { error?: string };
          console.error("[WS] Server error:", payload?.error);
          setState("idle");
          setIsFollowup(false);
          setStatusMessage("");
          break;
        }

        default:
          break;
      }
    };

    const client = new AssistantWebSocketClient(
      "ws://127.0.0.1:8765",
      handleWSMessage,
      (status) => setConnectionStatus(status),
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
      setWindowSize(440, 400);
    } else {
      setWindowSize(440, 130);
    }
  }, [response]);

  const cancelWorkflow = useCallback(() => {
    if (wsClientRef.current?.isConnected()) {
      wsClientRef.current.send("CLIENT_CANCEL");
    }
    setState("idle");
    setIsFollowup(false);
    setLiveTranscript("");
    setStatusMessage("");
  }, []);

  const clearSession = useCallback(() => {
    if (wsClientRef.current?.isConnected()) {
      wsClientRef.current.send("CLIENT_CLEAR_SESSION");
    }
    setResponse(null);
    setLiveTranscript("");
    setStatusMessage("");
    setIsFollowup(false);
    currentQueryRef.current = "";
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
      setLiveTranscript("");
      setStatusMessage("");
    } else {
      // If offline, attempt reconnecting
      wsClientRef.current?.connect();
    }
  };

  return (
    <div
      id="window-drag-region"
      className="w-full h-full flex flex-col justify-end items-center px-0.3 pb-0.3 bg-transparent select-none"
    >
      <div className="w-full flex flex-col items-center justify-end gap-1.5">
        {/* Streaming Response Card */}
        <AnimatePresence mode="sync">
          {response && (
            <ResponseCard
              response={response}
              onClose={() => {
                if (state !== "idle") {
                  cancelWorkflow();
                }
                clearSession();
              }}
              onDragStart={handleWindowDrag}
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
          statusMessage={statusMessage}
          onDragStart={handleWindowDrag}
        />
      </div>
    </div>
  );
}
