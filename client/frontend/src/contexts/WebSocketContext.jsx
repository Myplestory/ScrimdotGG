// WebSocket Context for Scrim.GG Client
// Manages WebSocket connection to local backend (localhost:5888)
// Optimized for performance - runs alongside Valorant

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';

const WebSocketContext = createContext(null);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  
  // State management
  const [authenticated, setAuthenticated] = useState(false);
  const [systemStatus, setSystemStatus] = useState({
    backend_connected: false,
    valorant: { status: 'unknown', message: 'Checking...' },
    authenticated: false
  });
  const [gameState, setGameState] = useState({
    status: 'disconnected', // disconnected, menus, in_party, in_pregame, in_match
    party_id: null,
    match_id: null,
  });
  const [playerData, setPlayerData] = useState(null);
  const [lobbyData, setLobbyData] = useState(null);
  const [matchData, setMatchData] = useState(null);
  const [queueStatus, setQueueStatus] = useState({ in_queue: false, estimated_wait: 0 });
  const [chatMessages, setChatMessages] = useState([]);
  
  // Event handlers registry
  const eventHandlers = useRef({});
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef(null);
  const maxReconnectAttempts = 5;
  const WS_URL = 'ws://localhost:5888/ws';

  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    if (socket?.readyState === WebSocket.OPEN || socket?.readyState === WebSocket.CONNECTING) {
      console.log('WebSocket already connected or connecting');
      return;
    }

    console.log('🔌 Connecting to local backend WebSocket...');
    const ws = new WebSocket(WS_URL);
    
    ws.onopen = () => {
      console.log('✅ WebSocket connected to local backend');
      setConnected(true);
      setReconnecting(false);
      setSocket(ws);
      reconnectAttempts.current = 0;
      
      // Send connected event to backend
      const message = JSON.stringify({ event: 'connected', payload: {} });
      ws.send(message);
    };
    
    ws.onclose = (event) => {
      console.log('❌ WebSocket disconnected:', event.code, event.reason);
      setConnected(false);
      setSocket(null);
      
      // Only attempt reconnection if it wasn't a clean close and we haven't exceeded max attempts
      if (!event.wasClean && reconnectAttempts.current < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000);
        console.log(`🔄 Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current + 1}/${maxReconnectAttempts})...`);
        setReconnecting(true);
        
        reconnectTimeout.current = setTimeout(() => {
          reconnectAttempts.current++;
          connectWebSocket();
        }, delay);
      } else if (reconnectAttempts.current >= maxReconnectAttempts) {
        console.error('❌ Max reconnection attempts reached');
        setReconnecting(false);
      } else {
        // Clean close, don't reconnect
        console.log('✅ WebSocket closed cleanly, not reconnecting');
        setReconnecting(false);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleEvent(data.event, data.payload);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
    
    setSocket(ws);
  }, [socket]);

  // Send event to backend
  const sendEvent = useCallback((event, payload = {}) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ event, payload });
      socket.send(message);
      console.log(`📤 Sent: ${event}`, payload);
      return true;
    } else {
      console.warn('⚠️ WebSocket not connected. Cannot send event:', event);
      return false;
    }
  }, [socket]);

  // Initialize connection on mount
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (socket) {
        socket.close(1000, 'Component unmounting'); // Clean close
      }
    };
  }, []); // Remove connectWebSocket from dependencies to prevent re-connection loops

  // Event handler router
  const handleEvent = useCallback((event, payload) => {
    console.log(`📥 Received: ${event}`, payload);
    
    // Built-in event handlers
    switch (event) {
      case 'connected':
        console.log('Backend confirmed connection');
        // Backend will automatically send status_update, no need to request it
        break;
        
      case 'status_update':
        console.log('📥 [FRONTEND] Received status_update:', payload);
        setSystemStatus(payload);
        setAuthenticated(payload.authenticated);
        break;
        
      case 'authentication_success':
        setAuthenticated(true);
        setPlayerData(payload.player_data);
        break;
        
      case 'game_state_change':
        setGameState(prev => ({ ...prev, ...payload }));
        break;
        
      case 'lobby_created':
      case 'lobby_updated':
        setLobbyData(payload);
        break;
        
      case 'lobby_message':
        setChatMessages(prev => [...prev, {
          user: payload.username,
          message: payload.message,
          timestamp: payload.timestamp,
          type: 'lobby'
        }]);
        break;
        
      case 'player_joined_lobby':
        setLobbyData(prev => ({
          ...prev,
          players: payload.players
        }));
        break;
        
      case 'player_left_lobby':
        setLobbyData(prev => ({
          ...prev,
          players: payload.players
        }));
        break;
        
      case 'queue_status':
        setQueueStatus(payload);
        break;
        
      case 'match_found':
        setMatchData(payload);
        break;
        
      case 'match_acceptance_required':
        setMatchData(prev => ({
          ...prev,
          requires_acceptance: true,
          acceptance_deadline: payload.deadline,
          map: payload.map,
          server: payload.server,
        }));
        break;
        
      case 'match_starting':
        setMatchData(prev => ({
          ...prev,
          status: 'starting',
          constructor_puuid: payload.constructor_puuid
        }));
        break;
        
      case 'match_ready':
        setMatchData(prev => ({
          ...prev,
          status: 'ready',
          pregame_id: payload.pregame_id
        }));
        break;
        
      case 'match_cancelled':
        setMatchData(null);
        setQueueStatus({ in_queue: false, estimated_wait: 0 });
        break;
        
      case 'match_completed':
        setMatchData(prev => ({
          ...prev,
          status: 'completed',
          results: payload.results
        }));
        break;
        
      case 'error':
        console.error('❌ Server error:', payload.message);
        break;
        
      default:
        // Check for custom event handlers
        if (eventHandlers.current[event]) {
          eventHandlers.current[event](payload);
        }
    }
  }, []);

  // Register custom event handler
  const on = useCallback((event, handler) => {
    eventHandlers.current[event] = handler;
    return () => {
      delete eventHandlers.current[event];
    };
  }, []);

  // API methods (replaces all REST calls)
  const api = {
    // Authentication
    authenticate: () => sendEvent('authenticate', {}),
    
    // Lobby operations
    createLobby: () => sendEvent('create_lobby', {}),
    joinLobby: (lobbyId) => sendEvent('join_lobby', { lobby_id: lobbyId }),
    leaveLobby: () => sendEvent('leave_lobby', {}),
    inviteToLobby: (puuid) => sendEvent('invite_to_lobby', { puuid }),
    kickFromLobby: (puuid) => sendEvent('kick_from_lobby', { puuid }),
    
    // Queue operations
    queueLobby: (mapPreferences, serverPreferences) => sendEvent('queue_lobby', {
      map_preferences: mapPreferences,
      server_preferences: serverPreferences
    }),
    dequeueLobby: () => sendEvent('dequeue_lobby', {}),
    
    // Match operations
    acceptMatch: (matchId) => sendEvent('accept_match', { match_id: matchId }),
    declineMatch: (matchId) => sendEvent('decline_match', { match_id: matchId }),
    
    // Chat operations
    sendLobbyMessage: (message, lobbyId) => sendEvent('lobby_chat', {
      message,
      lobby_id: lobbyId,
      timestamp: new Date().toISOString()
    }),
    sendDirectMessage: (recipientPuuid, message) => sendEvent('direct_message', {
      recipient_puuid: recipientPuuid,
      message,
      timestamp: new Date().toISOString()
    }),
    
    // Player operations
    getPlayerData: () => sendEvent('get_player_data', {}),
    updatePlayerSettings: (settings) => sendEvent('update_settings', settings),
  };

  const value = {
    // Connection state
    connected,
    reconnecting,
    authenticated,
    systemStatus,
    
    // Game state
    gameState,
    playerData,
    lobbyData,
    matchData,
    queueStatus,
    chatMessages,
    
    // Methods
    sendEvent,
    on,
    api,
    
    // Manual reconnect
    reconnect: connectWebSocket,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

