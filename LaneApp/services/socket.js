import io from 'socket.io-client';

// Backend URL (Elastic IP)
const SOCKET_URL = 'http://lane-alb-244971260.ap-northeast-2.elb.amazonaws.com:5000';

export const socket = io(SOCKET_URL, {
  transports: ['websocket'], // Force WebSocket to avoid polling issues
  reconnection: true,
  reconnectionAttempts: 5,
});
