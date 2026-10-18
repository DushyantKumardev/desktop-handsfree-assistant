export type AssistantState =
  | 'idle'
  | 'listening'
  | 'thinking'
  | 'speaking'
  | 'minimized';

export interface AssistantResponse {
  id: string;
  query: string;
  content: string;
  isStreaming: boolean;
  timestamp: string;
}

export type WSEventType =
  | 'CLIENT_AUDIO_CHUNK'
  | 'CLIENT_COMMAND'
  | 'CLIENT_CANCEL'
  | 'CLIENT_TRIGGER_LISTEN'
  | 'SERVER_SHOW_WIDGET'
  | 'SERVER_STATE_CHANGE'
  | 'SERVER_TRANSCRIPTION'
  | 'SERVER_STREAM_CHUNK'
  | 'SERVER_RESPONSE_COMPLETE'
  | 'SERVER_NOTIFICATION'
  | 'SERVER_ERROR'
  | 'PING'
  | 'PONG';

export interface WSMessage<T = unknown> {
  type: WSEventType;
  payload: T;
  timestamp: number;
}
