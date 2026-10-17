import type { WSEventType, WSMessage } from "../types/assistant";

export type ConnectionStatus = "connected" | "connecting" | "disconnected";

export class AssistantWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private reconnectInterval = 1000;
  private pingIntervalId?: number;
  private onMessageCallback: (msg: WSMessage) => void;
  private onStatusChangeCallback: (status: ConnectionStatus) => void;

  constructor(
    url: string,
    onMessage: (msg: WSMessage) => void,
    onStatusChange: (status: ConnectionStatus) => void,
  ) {
    this.url = url;
    this.onMessageCallback = onMessage;
    this.onStatusChangeCallback = onStatusChange;
  }

  public isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  public connect(): void {
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.OPEN ||
        this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    this.onStatusChangeCallback("connecting");

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.onStatusChangeCallback("connected");
        this.startHeartbeat();
      };

      this.ws.onmessage = (event) => {
        try {
          const data: WSMessage = JSON.parse(event.data);
          if (data.type === "PONG") return;
          this.onMessageCallback(data);
        } catch (err) {
          console.error("[WebSocket] Error parsing event:", err);
        }
      };

      this.ws.onclose = () => {
        this.stopHeartbeat();
        this.onStatusChangeCallback("disconnected");
        this.scheduleReconnect();
      };

      this.ws.onerror = (err) => {
        console.warn("[WebSocket] Connection error:", err);
        this.ws?.close();
      };
    } catch (err) {
      console.warn("[WebSocket] Initialization failed:", err);
      this.scheduleReconnect();
    }
  }

  public send(type: WSEventType, payload: unknown = {}): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message: WSMessage = {
        type,
        payload,
        timestamp: Date.now(),
      };
      this.ws.send(JSON.stringify(message));
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.pingIntervalId = window.setInterval(() => {
      this.send("PING");
    }, 15000);
  }

  private stopHeartbeat(): void {
    if (this.pingIntervalId) {
      clearInterval(this.pingIntervalId);
      this.pingIntervalId = undefined;
    }
  }

  private isExplicitDisconnect = false;

  private scheduleReconnect(): void {
    if (this.isExplicitDisconnect) return;
    const delay = Math.min(
      this.reconnectInterval * Math.pow(1.3, this.reconnectAttempts),
      4000,
    );
    this.reconnectAttempts++;
    setTimeout(() => {
      if (!this.isExplicitDisconnect) {
        this.connect();
      }
    }, delay);
  }

  public disconnect(): void {
    this.isExplicitDisconnect = true;
    this.stopHeartbeat();
    this.ws?.close();
    this.ws = null;
  }
}
