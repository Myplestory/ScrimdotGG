// WebSocket Context for Scrim.GG Client
// Manages WebSocket connection to local backend (localhost:5888)
// Optimized for performance - runs alongside Valorant

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';

const WebSocketContext = createContext(null);

export { WebSocketContext };

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
  
  // Match state validation tracking
  const [matchStateInfo, setMatchStateInfo] = useState({
    inActiveMatch: false,
    matchId: null,
    matchState: null,
    canQueue: true,
    blockedReason: null
  });
  
  // Event handlers registry
  const eventHandlers = useRef({});
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef(null);
  const maxReconnectAttempts = 10; // Increased from 5 to 10 for better resilience
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
      
      // Show success notification if this was a reconnection
      if (reconnectAttempts.current > 0) {
        console.log(`✅ Successfully reconnected after ${reconnectAttempts.current} attempts`);
        if (window.showNotification) {
          window.showNotification({
            type: 'success',
            title: 'Reconnected',
            message: 'Connection to server restored',
            duration: 3000
          });
        }
      }
      
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
        
        // Show user notification about reconnection
        if (window.showNotification) {
          window.showNotification({
            type: 'warning',
            title: 'Connection Lost',
            message: `Reconnecting... (${reconnectAttempts.current + 1}/${maxReconnectAttempts})`,
            duration: delay
          });
        }
        
        reconnectTimeout.current = setTimeout(() => {
          reconnectAttempts.current++;
          connectWebSocket();
        }, delay);
      } else if (reconnectAttempts.current >= maxReconnectAttempts) {
        console.error('❌ Max reconnection attempts reached');
        setReconnecting(false);
        
        // Show user notification about failed reconnection
        if (window.showNotification) {
          window.showNotification({
            type: 'error',
            title: 'Connection Failed',
            message: 'Unable to reconnect to server. Please refresh the page.',
            duration: 0 // Persistent notification
          });
        }
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
        
      case 'queue_eligibility':
        console.log('📥 [FRONTEND] Queue eligibility check:', payload);
        setMatchStateInfo(prev => ({
          ...prev,
          canQueue: payload.can_queue,
          blockedReason: payload.reason || null,
          inActiveMatch: !payload.can_queue,
          matchId: payload.match_id || null,
          matchState: payload.match_state || null
        }));
        break;
        
      case 'queue_blocked':
        console.log('📥 [FRONTEND] Queue blocked:', payload);
        setMatchStateInfo(prev => ({
          ...prev,
          canQueue: false,
          blockedReason: payload.message,
          inActiveMatch: true
        }));
        
        // Show notification to user
        if (window.showNotification) {
          window.showNotification({
            type: 'error',
            title: 'Cannot Queue',
            message: payload.message,
            details: payload.blocked_players ? 
              `Blocked players: ${payload.blocked_players.join(', ')}` : null
          });
        }
        break;
        
      case 'match_state_changed':
        console.log('📥 [FRONTEND] Match state changed:', payload);
        setMatchStateInfo(prev => ({
          ...prev,
          inActiveMatch: !payload.can_queue,
          matchId: payload.match_id,
          matchState: payload.state,
          canQueue: payload.can_queue
        }));
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
        
      case 'match_data':
        console.log('📥 [FRONTEND] Received match data:', payload);
        setMatchData(payload);
        // Call custom event handler if registered
        if (eventHandlers.current['match_data']) {
          eventHandlers.current['match_data'](payload);
        }
        break;
        
      case 'server_veto_complete':
        console.log('📥 [FRONTEND] Server veto phase completed:', payload);
        setMatchData(prev => ({
          ...prev,
          state: 'VETO', // Transition to map veto phase
          final_server: payload.final_server,
          map_pool: payload.available_maps,
          veto_turn: payload.current_turn,
          veto_deadline: payload.veto_deadline,
          vetoed_maps: [], // Reset vetoed maps for map veto phase
          veto_state: {
            ...prev?.veto_state,
            server_veto_complete: true,
            final_server: payload.final_server,
            current_turn: payload.current_turn,
            available_maps: payload.available_maps,
            veto_deadline: payload.veto_deadline,
            last_update: Date.now()
          }
        }));
        // Call custom event handler if registered
        if (eventHandlers.current['server_veto_complete']) {
          eventHandlers.current['server_veto_complete'](payload);
        }
        break;
        
      case 'map_veto_started':
        console.log('📥 [FRONTEND] Map veto phase started:', payload);
        setMatchData(prev => ({
          ...prev,
          state: 'VETO', // Ensure we're in map veto phase
          map_pool: payload.available_maps || prev?.map_pool,
          veto_turn: payload.current_turn,
          veto_deadline: payload.deadline,
          vetoed_maps: [], // Reset vetoed maps for map veto phase
          veto_state: {
            ...prev?.veto_state,
            map_veto_started: true,
            current_turn: payload.current_turn,
            available_maps: payload.available_maps || prev?.map_pool,
            veto_deadline: payload.deadline,
            last_update: Date.now()
          }
        }));
        // Call custom event handler if registered
        if (eventHandlers.current['map_veto_started']) {
          eventHandlers.current['map_veto_started'](payload);
        }
        break;
        
      case 'map_vetoed':
        console.log('📥 [FRONTEND] Received map vetoed:', payload);
        console.log('🔄 [WEBSOCKET] Before state update - matchData:', matchData);
        console.log('🔄 [WEBSOCKET] Before state update - veto_state:', matchData?.veto_state);
        
        setMatchData(prev => {
          const newState = {
            ...prev,
            veto_state: {
              ...prev?.veto_state,
              vetoed_map: payload.map,
              vetoed_by: payload.vetoed_by,
              current_turn: payload.next_turn,
              remaining_maps: payload.remaining_maps,
              last_update: Date.now()
            }
          };
          
          console.log('🔄 [WEBSOCKET] After state update - newState:', newState);
          console.log('🔄 [WEBSOCKET] After state update - veto_state:', newState.veto_state);
          
          return newState;
        });
        
        // Call custom event handler if registered
        if (eventHandlers.current['map_vetoed']) {
          eventHandlers.current['map_vetoed'](payload);
        }
        break;
        
      case 'veto_complete':
        console.log('📥 [FRONTEND] Veto phase completed:', payload);
        setMatchData(prev => ({
          ...prev,
          veto_state: {
            ...prev?.veto_state,
            completed: true,
            final_map: payload.final_map
          }
        }));
        // Call custom event handler if registered
        if (eventHandlers.current['veto_complete']) {
          eventHandlers.current['veto_complete'](payload);
        }
        break;
        
      case 'server_veto_timeout':
        console.log('📥 [FRONTEND] Server veto timeout:', payload);
        setMatchData(prev => ({
          ...prev,
          veto_state: {
            ...prev?.veto_state,
            server_veto_timeout: true,
            auto_vetoed_server: payload.auto_vetoed_server,
            server_veto_complete: payload.server_veto_complete,
            final_server: payload.final_server,
            current_turn: payload.current_turn,
            available_maps: payload.available_maps,
            veto_deadline: payload.veto_deadline,
            last_update: Date.now()
          }
        }));
        // Call custom event handler if registered
        if (eventHandlers.current['server_veto_timeout']) {
          eventHandlers.current['server_veto_timeout'](payload);
        }
        break;
        
      case 'map_veto_timeout':
        console.log('📥 [FRONTEND] Map veto timeout:', payload);
        setMatchData(prev => ({
          ...prev,
          veto_state: {
            ...prev?.veto_state,
            map_veto_timeout: true,
            auto_vetoed_map: payload.auto_vetoed_map,
            veto_complete: payload.veto_complete,
            current_turn: payload.next_turn,
            remaining_maps: payload.remaining_maps,
            final_map: payload.final_map,
            last_update: Date.now()
          }
        }));
        // Call custom event handler if registered
        if (eventHandlers.current['map_veto_timeout']) {
          eventHandlers.current['map_veto_timeout'](payload);
        }
        break;
        
      case 'side_selection_timeout':
        console.log('📥 [FRONTEND] Side selection timeout:', payload);
        setMatchData(prev => ({
          ...prev,
          veto_state: {
            ...prev?.veto_state,
            side_selection_timeout: true,
            auto_selected_side: payload.auto_selected_side,
            side_selection_complete: payload.side_selection_complete,
            match_ready: payload.match_ready,
            last_update: Date.now()
          }
        }));
        // Call custom event handler if registered
        if (eventHandlers.current['side_selection_timeout']) {
          eventHandlers.current['side_selection_timeout'](payload);
        }
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
    
    // PUG Queue operations
    joinPugQueue: (queueData) => sendEvent('join_pug_queue', queueData),
    leavePugQueue: () => sendEvent('leave_pug_queue', {}),
    
    // Lobby Invite operations
    sendLobbyInvite: (lobbyId, targetPlayerPuuid) => sendEvent('send_lobby_invite', {
      lobby_id: lobbyId,
      target_player_puuid: targetPlayerPuuid
    }),
    acceptLobbyInvite: (inviteId) => sendEvent('accept_lobby_invite', { invite_id: inviteId }),
    declineLobbyInvite: (inviteId) => sendEvent('decline_lobby_invite', { invite_id: inviteId }),
    getAvailablePlayers: (filters = {}) => sendEvent('get_available_players', { filters }),
  };

  // Helper function to check queue eligibility
  const checkQueueEligibility = useCallback((lobbyId = null, playerPuuid = null) => {
    if (!connected) return;
    
    const payload = {};
    if (lobbyId) payload.lobby_id = lobbyId;
    if (playerPuuid) payload.player_puuid = playerPuuid;
    
    sendEvent('check_queue_eligibility', payload);
  }, [connected, sendEvent]);

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
    matchStateInfo,
    
    // Methods
    sendEvent,
    on,
    api,
    checkQueueEligibility,
    
    // Manual reconnect
    reconnect: () => {
      // Reset reconnection attempts for manual reconnect
      reconnectAttempts.current = 0;
      setReconnecting(false);
      connectWebSocket();
    },
    
    // Reset reconnection state
    resetReconnection: () => {
      reconnectAttempts.current = 0;
      setReconnecting(false);
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
        reconnectTimeout.current = null;
      }
    },
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

