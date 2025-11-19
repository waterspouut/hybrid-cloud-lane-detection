import io from 'socket.io-client';

// Backend URL (Elastic IP)
const SOCKET_URL = 'http://15.165.177.0:5000';

export const socket = io(SOCKET_URL, {
  transports: ['websocket'], // Force WebSocket to avoid polling issues
  reconnection: true,
  reconnectionAttempts: 5,
});
