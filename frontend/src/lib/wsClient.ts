import { useCallback, useRef } from "react";
import { useSimulationStore } from "@/stores/simulation";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:3301";

export function useWSClient() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const addEvent = useSimulationStore((s) => s.addEvent);

  const connect = useCallback(
    (worldId: string) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;

      const ws = new WebSocket(`${WS_URL}/ws/${worldId}`);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          addEvent(data);
        } catch {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        // Reconnect after 3s
        reconnectTimer.current = setTimeout(() => connect(worldId), 3000);
      };

      ws.onerror = () => {
        ws.close();
      };
    },
    [addEvent]
  );

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current);
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  return { connect, disconnect };
}
