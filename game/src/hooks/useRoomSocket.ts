import { useCallback, useEffect, useRef, useState } from "react";
import type { RoomState } from "../types";

const STORAGE_CODE_KEY = "defense_room_code";
const STORAGE_TOKEN_KEY = "defense_player_token";
const RECONNECT_DELAY_MS = 1800;

function safeStore(code: string, token: string): void {
  try {
    localStorage.setItem(STORAGE_CODE_KEY, code);
    localStorage.setItem(STORAGE_TOKEN_KEY, token);
  } catch {
    // Private browsing may disable storage.
  }
}

function clearStoredRoom(): void {
  try {
    localStorage.removeItem(STORAGE_CODE_KEY);
    localStorage.removeItem(STORAGE_TOKEN_KEY);
  } catch {
    // ignore
  }
}

function readStoredRoom(): { code: string; token: string } | null {
  try {
    const code = localStorage.getItem(STORAGE_CODE_KEY);
    const token = localStorage.getItem(STORAGE_TOKEN_KEY);
    return code && token ? { code, token } : null;
  } catch {
    return null;
  }
}

function socketUrl(code: string): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/${encodeURIComponent(code)}`;
}

export interface RoomSocketState {
  roomState: RoomState | null;
  connected: boolean;
  roomCode: string | null;
  knownHost: boolean;
  waitingForAnswerAck: boolean;
  actionError: string | null;
  actionErrorReason: string | null;
  sendEvent: (payload: Record<string, unknown>) => boolean;
  useRoom: (code: string, token: string, host: boolean) => void;
  leaveRoom: () => void;
  playerToken: string | null;
}

export function useRoomSocket(previewMode: boolean): RoomSocketState {
  const [roomState, setRoomState] = useState<RoomState | null>(null);
  const [connected, setConnected] = useState(false);
  const [roomCode, setRoomCode] = useState<string | null>(null);
  const [knownHost, setKnownHost] = useState(false);
  const [waitingForAnswerAck, setWaitingForAnswerAck] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionErrorReason, setActionErrorReason] = useState<string | null>(null);

  const playerTokenRef = useRef<string | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const connectionVersionRef = useRef(0);
  const roomCodeRef = useRef<string | null>(null);
  const pendingAnswerTurnRef = useRef<number | null>(null);

  // Keep roomCodeRef in sync for connectSocket closure
  useEffect(() => {
    roomCodeRef.current = roomCode;
  }, [roomCode]);

  const connectSocket = useCallback(() => {
    if (previewMode || !roomCodeRef.current || !playerTokenRef.current) return;
    const version = ++connectionVersionRef.current;
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    if (websocketRef.current) websocketRef.current.close();
    setConnected(false);

    let socket: WebSocket;
    try {
      socket = new WebSocket(socketUrl(roomCodeRef.current));
    } catch {
      reconnectTimerRef.current = setTimeout(
        () => {
          if (version === connectionVersionRef.current) connectSocket();
        },
        RECONNECT_DELAY_MS,
      );
      return;
    }
    websocketRef.current = socket;

    socket.addEventListener("open", () => {
      if (version !== connectionVersionRef.current) return;
      setConnected(true);
      socket.send(
        JSON.stringify({ type: "hello", token: playerTokenRef.current }),
      );
    });

    socket.addEventListener("message", (event: MessageEvent) => {
      if (version !== connectionVersionRef.current) return;
      let message: Record<string, unknown>;
      try {
        message = JSON.parse(String(event.data)) as Record<string, unknown>;
      } catch {
        return;
      }
      if (message.type === "snapshot" && message.state) {
        const snapshot = message.state as RoomState;
        setRoomState(snapshot);
        setActionError(null);
        setActionErrorReason(null);
        const pendingTurn = pendingAnswerTurnRef.current;
        if (pendingTurn !== null && (snapshot.turns[pendingTurn]?.answer != null || snapshot.phase !== "question")) {
          pendingAnswerTurnRef.current = null;
          setWaitingForAnswerAck(false);
        }
      } else if (message.type === "error") {
        const errMsg = String(message.message ?? "Room action failed.");
        pendingAnswerTurnRef.current = null;
        setWaitingForAnswerAck(false);
        setActionError(errMsg);
        setActionErrorReason(typeof message.reason === "string" ? message.reason : null);
        if (
          errMsg.startsWith("Room not found.") ||
          errMsg.startsWith("This room link is no longer valid.")
        ) {
          // Trigger full leave via the state reset path
          connectionVersionRef.current++;
          if (reconnectTimerRef.current)
            clearTimeout(reconnectTimerRef.current);
          if (websocketRef.current) websocketRef.current.close();
          websocketRef.current = null;
          setConnected(false);
          setRoomCode(null);
          roomCodeRef.current = null;
          playerTokenRef.current = null;
          setRoomState(null);
          setKnownHost(false);
          setWaitingForAnswerAck(false);
          clearStoredRoom();
        }
      }
    });

    socket.addEventListener("close", () => {
      if (version !== connectionVersionRef.current) return;
      setConnected(false);
      pendingAnswerTurnRef.current = null;
      setWaitingForAnswerAck(false);
      reconnectTimerRef.current = setTimeout(
        () => {
          if (version === connectionVersionRef.current) connectSocket();
        },
        RECONNECT_DELAY_MS,
      );
    });
  }, [previewMode]); // eslint-disable-line react-hooks/exhaustive-deps

  // A healthy socket already receives authoritative snapshots. Replacing it
  // would disconnect the chosen defender and trigger speaker reassignment.
  useEffect(() => {
    const resume = () => {
      if (websocketRef.current?.readyState !== WebSocket.OPEN) connectSocket();
    };
    window.addEventListener("defense-native-resume", resume);
    return () => window.removeEventListener("defense-native-resume", resume);
  }, [connectSocket]);

  const useRoom = useCallback(
    (code: string, token: string, host: boolean) => {
      const upperCode = code.toUpperCase();
      roomCodeRef.current = upperCode;
      playerTokenRef.current = token;
      setRoomCode(upperCode);
      setKnownHost(host);
      setRoomState(null);
      pendingAnswerTurnRef.current = null;
      setWaitingForAnswerAck(false);
      setActionError(null);
      setActionErrorReason(null);
      safeStore(upperCode, token);
      connectSocket();
    },
    [connectSocket],
  );

  const leaveRoom = useCallback(() => {
    connectionVersionRef.current++;
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    reconnectTimerRef.current = null;
    if (websocketRef.current) websocketRef.current.close();
    websocketRef.current = null;
    setConnected(false);
    setRoomCode(null);
    roomCodeRef.current = null;
    playerTokenRef.current = null;
    setRoomState(null);
    setKnownHost(false);
    pendingAnswerTurnRef.current = null;
    setWaitingForAnswerAck(false);
    setActionError(null);
    setActionErrorReason(null);
    clearStoredRoom();
  }, []);

  const sendEvent = useCallback(
    (payload: Record<string, unknown>): boolean => {
      const ws = websocketRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) return false;
      if ((payload.type === "submit_answer" || payload.type === "submit_direct_answer")) {
        if (pendingAnswerTurnRef.current !== null) return false;
        pendingAnswerTurnRef.current = Number(payload.turn);
        setWaitingForAnswerAck(true);
      }
      setActionError(null);
      setActionErrorReason(null);
      try {
        ws.send(JSON.stringify(payload));
        return true;
      } catch {
        if ((payload.type === "submit_answer" || payload.type === "submit_direct_answer")) {
          pendingAnswerTurnRef.current = null;
          setWaitingForAnswerAck(false);
        }
        return false;
      }
    },
    [],
  );

  // On mount: attempt to restore a stored room
  useEffect(() => {
    if (previewMode) return;
    const stored = readStoredRoom();
    if (stored) {
      useRoom(stored.code, stored.token, false);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      connectionVersionRef.current++;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (websocketRef.current) websocketRef.current.close();
    };
  }, []);

  return {
    roomState,
    connected,
    roomCode,
    knownHost,
    waitingForAnswerAck,
    actionError,
    actionErrorReason,
    sendEvent,
    useRoom,
    leaveRoom,
    playerToken: playerTokenRef.current,
  };
}
