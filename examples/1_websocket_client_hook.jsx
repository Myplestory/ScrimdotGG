// Scrim.GG_Client/scrimgg/frontend/scrimgg/src/hooks/useWebSocket.js
// Modern WebSocket hook for React - replaces REST API calls

import { useState, useEffect, useCallback, useRef, createContext, useContext } from 'react';

// WebSocket Context
const WebSocketContext = createContext(null);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
};

// WebSocket Provider Component
export const WebSocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
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
  
  const eventHandlers = useRef({});
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  // Connect to local backend WebSocket
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const ws = new WebSocket('ws://localhost:5888/ws');
    
    ws.onopen = () => {
      console.log('WebSocket connected to local backend');
      setConnected(true);
      setSocket(ws);
      reconnectAttempts.current = 0;
      
      // Request initial state
      sendEvent('get_initial_state', {});
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      setSocket(null);
      
      // Attempt reconnection with exponential backoff
      if (reconnectAttempts.current < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000);
        console.log(`Reconnecting in ${delay}ms...`);
        setTimeout(() => {
          reconnectAttempts.current++;
          connectWebSocket();
        }, delay);
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
  };

  // Event handler router
  const handleEvent = useCallback((event, payload) => {
    console.log(`Received event: ${event}`, payload);
    
    // Built-in event handlers
    switch (event) {
      case 'authentication_success':
        setPlayerData(payload.player_data);
        break;
        
      case 'game_state_change':
        setGameState(prev => ({ ...prev, ...payload }));
        break;
        
      case 'lobby_created':
      case 'lobby_updated':
        setLobbyData(payload);
        break;
        
      case 'match_found':
        setMatchData(payload);
        break;
        
      case 'queue_status':
        setQueueStatus(payload);
        break;
        
      case 'lobby_message':
        setChatMessages(prev => [...prev, {
          user: payload.username,
          message: payload.message,
          timestamp: payload.timestamp,
          type: 'lobby'
        }]);
        break;
        
      case 'direct_message':
        setChatMessages(prev => [...prev, {
          user: payload.username,
          message: payload.message,
          timestamp: payload.timestamp,
          type: 'dm'
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
        
      case 'match_acceptance_required':
        // Show match acceptance modal
        setMatchData(prev => ({
          ...prev,
          requires_acceptance: true,
          acceptance_deadline: payload.deadline
        }));
        break;
        
      case 'match_starting':
        // Constructor is creating the custom game
        setMatchData(prev => ({
          ...prev,
          status: 'starting',
          constructor_puuid: payload.constructor_puuid
        }));
        break;
        
      case 'match_ready':
        // Custom game created, join now
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
        
      case 'error':
        console.error('Server error:', payload.message);
        break;
        
      default:
        // Check for custom event handlers
        if (eventHandlers.current[event]) {
          eventHandlers.current[event](payload);
        }
    }
  }, []);

  // Send event to backend
  const sendEvent = useCallback((event, payload = {}) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ event, payload });
      socket.send(message);
      console.log(`Sent event: ${event}`, payload);
    } else {
      console.error('WebSocket not connected. Cannot send event:', event);
    }
  }, [socket]);

  // Register custom event handler
  const on = useCallback((event, handler) => {
    eventHandlers.current[event] = handler;
    return () => {
      delete eventHandlers.current[event];
    };
  }, []);

  // API methods (replace old REST calls)
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
    
    // Veto operations
    banMap: (matchId, map) => sendEvent('veto_ban_map', { match_id: matchId, map }),
    pickMap: (matchId, map) => sendEvent('veto_pick_map', { match_id: matchId, map }),
    banServer: (matchId, server) => sendEvent('veto_ban_server', { match_id: matchId, server }),
    pickServer: (matchId, server) => sendEvent('veto_pick_server', { match_id: matchId, server }),
    
    // Chat operations
    sendLobbyMessage: (message) => sendEvent('lobby_chat', {
      message,
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
    connected,
    gameState,
    playerData,
    lobbyData,
    matchData,
    queueStatus,
    chatMessages,
    sendEvent,
    on,
    api,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

// Example usage in a component:
/*
function LobbyComponent() {
  const { lobbyData, api, on } = useWebSocket();
  
  useEffect(() => {
    // Register custom event handler
    const unsubscribe = on('custom_event', (payload) => {
      console.log('Custom event received:', payload);
    });
    
    return unsubscribe;
  }, [on]);
  
  const handleCreateLobby = () => {
    api.createLobby();
  };
  
  const handleQueue = () => {
    api.queueLobby(['Ascent', 'Haven'], ['NA-East']);
  };
  
  return (
    <div>
      <button onClick={handleCreateLobby}>Create Lobby</button>
      {lobbyData && (
        <div>
          <h2>Lobby: {lobbyData.id}</h2>
          <button onClick={handleQueue}>Queue Up</button>
        </div>
      )}
    </div>
  );
}
*/

