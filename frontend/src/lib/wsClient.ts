import { useCallback, useRef } from "react";
import { useSimulationStore } from "@/stores/simulation";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:3301";

const MAX_RETRIES = 10;
const BASE_DELAY_MS = 2_000;
const MAX_DELAY_MS = 30_000;

export function useWSClient() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const retryCount = useRef(0);
  const addEvent = useSimulationStore((s) => s.addEvent);

  const connect = useCallback(
    (worldId: string) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;

      const ws = new WebSocket(`${WS_URL}/ws/${worldId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        retryCount.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          addEvent(data);
        } catch (err) {
          console.warn("[WS] Failed to parse message:", err);
        }
      };

      ws.onclose = (event) => {
        wsRef.current = null;

        if (retryCount.current >= MAX_RETRIES) {
          console.error(
            `[WS] Gave up reconnecting after ${MAX_RETRIES} attempts`
          );
          return;
        }

        const delay = Math.min(
          BASE_DELAY_MS * Math.pow(2, retryCount.current),
          MAX_DELAY_MS
        );
        retryCount.current += 1;

        console.log(
          `[WS] Closed (code=${event.code}). Reconnecting in ${delay}ms (attempt ${retryCount.current}/${MAX_RETRIES})`
        );
        reconnectTimer.current = setTimeout(() => connect(worldId), delay);
      };

      ws.onerror = (event) => {
        console.error("[WS] Error:", event);
        ws.close();
      };
    },
    [addEvent]
  );

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current);
    retryCount.current = 0;
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  return { connect, disconnect };
}
