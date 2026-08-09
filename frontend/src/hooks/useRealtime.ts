import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getAccessToken } from "../services/apiClient";
import {
  applyRealtimeEvent,
  realtimeClient,
  type ConnectionState,
  type RealtimeEvent,
} from "../services/realtimeClient";
import { useAuth } from "./useAuth";

interface RealtimeContextValue {
  connectionState: ConnectionState;
  lastEvent: RealtimeEvent | null;
  subscribeOrder: (orderId: string) => void;
}

const RealtimeContext = createContext<RealtimeContextValue | undefined>(undefined);

export function RealtimeProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [connectionState, setConnectionState] = useState<ConnectionState>("disconnected");
  const [lastEvent, setLastEvent] = useState<RealtimeEvent | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!user || !token) {
      realtimeClient.disconnect();
      return;
    }

    realtimeClient.connect(token);
    const unsubscribeEvents = realtimeClient.subscribe((event) => {
      setLastEvent(event);
      applyRealtimeEvent(queryClient, event);
    });
    const unsubscribeState = realtimeClient.onStateChange(setConnectionState);

    return () => {
      unsubscribeEvents();
      unsubscribeState();
      realtimeClient.disconnect();
    };
  }, [user, queryClient]);

  const value = useMemo<RealtimeContextValue>(
    () => ({
      connectionState,
      lastEvent,
      subscribeOrder: (orderId: string) => realtimeClient.subscribeOrder(orderId),
    }),
    [connectionState, lastEvent],
  );

  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
}

export function useRealtime(): RealtimeContextValue {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error("useRealtime must be used within RealtimeProvider");
  }
  return context;
}
