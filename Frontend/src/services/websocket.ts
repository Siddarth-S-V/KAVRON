const WS_BASE_URL =
  import.meta.env.VITE_WS_URL ||
  "ws://127.0.0.1:8000";

export type KavronWebSocket = WebSocket & {
  __kavronClosing?: boolean;
};

export function connectKavronEvents(
  onMessage: (data: any) => void,
  onError?: (event: Event) => void,
) {
  const wsEndpoint =
    import.meta.env.VITE_WS_PATH ||
    "/ws/events";

  const normalizedBase = WS_BASE_URL.replace(/\/$/, "");
  const normalizedPath = wsEndpoint.startsWith("/")
    ? wsEndpoint
    : `/${wsEndpoint}`;

  const socket = new WebSocket(
    `${normalizedBase}${normalizedPath}`,
  ) as KavronWebSocket;

  socket.__kavronClosing = false;

  socket.onopen = () => {
    console.log("🟢 KAVRON WebSocket connected");
  };

  socket.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data));
    } catch (error) {
      console.error("Invalid KAVRON WebSocket payload:", error);
    }
  };

  socket.onerror = (event) => {
    // React StrictMode can close a CONNECTING socket during effect cleanup.
    // Do not turn that expected development cleanup into a red error.
    if (socket.__kavronClosing) return;

    console.error("🔴 KAVRON WebSocket error");
    onError?.(event);
  };

  socket.onclose = () => {
    if (socket.__kavronClosing) return;
    console.log("🟡 KAVRON WebSocket disconnected");
  };

  return socket;
}

export function closeKavronEvents(socket: WebSocket | null | undefined) {
  if (!socket) return;

  const typed = socket as KavronWebSocket;
  typed.__kavronClosing = true;

  if (
    socket.readyState === WebSocket.OPEN ||
    socket.readyState === WebSocket.CONNECTING
  ) {
    try {
      socket.close(1000, "KAVRON page cleanup");
    } catch {
      // Browser may already have transitioned the socket state.
    }
  }
}
