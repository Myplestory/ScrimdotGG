// PugQueue.jsx - Main PUG queue screen (FACEIT-like)
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Avatar,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
  IconButton,
  Badge,
  TextField,
  Container,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Timer,
  People,
  Star,
  Flag,
  TrendingUp,
  TrendingDown,
  Search,
  Add,
  Person
} from '@mui/icons-material';
import { useMode } from '../../theme';
import { useWebSocket } from '../../contexts/WebSocketContext';
import PlayerSlot from '../../components/lobby/playerslot';

const PugQueue = () => {
  const [theme, colorMode] = useMode();
  const navigate = useNavigate();
  const [queueStatus, setQueueStatus] = useState({
    in_queue: false,
    queue_type: null,
    estimated_wait: 0,
    players_in_queue: 0
  });
  const [matchFound, setMatchFound] = useState(false);
  const [matchData, setMatchData] = useState(null);
  const [timeLeft, setTimeLeft] = useState(30);
  const [acceptedCount, setAcceptedCount] = useState(0);
  const [totalPlayers, setTotalPlayers] = useState(10);
  const [userAccepted, setUserAccepted] = useState(false);
  
  // Preview mode for testing modal design
  useEffect(() => {
    const handlePreview = () => {
      setMatchFound(true);
      setTimeLeft(30);
      setMatchData({
        match_id: 'preview-123',
        timeout_seconds: 30,
        message: 'Preview match found!'
      });
    };
    
    window.addEventListener('preview-match-modal', handlePreview);
    return () => window.removeEventListener('preview-match-modal', handlePreview);
  }, []);
  const [selectedQueueType, setSelectedQueueType] = useState('pug');
  const [selectedMaps, setSelectedMaps] = useState([]);
  const [selectedServers, setSelectedServers] = useState([]);
  const [players, setPlayers] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [activeTab, setActiveTab] = useState('maps'); // 'maps', 'match_type', 'servers'
  const [queueStartTime, setQueueStartTime] = useState(null);
  const messagesEndRef = useRef(null);
  
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [availablePlayers, setAvailablePlayers] = useState([]);
  const [invitingPlayer, setInvitingPlayer] = useState(null);
  const [loadingPlayers, setLoadingPlayers] = useState(false);
  const [inviteError, setInviteError] = useState(null);
  
  // Match Found Banner state - Triggered by WebSocket 'match_found_banner' event
  const [showMatchBanner, setShowMatchBanner] = useState(true); // Set to true for testing (false in production)
  const [matchBannerData, setMatchBannerData] = useState({
    map: 'Corrode', // Test data - will be populated by WebSocket
    match_id: null,
    server: null
  });
  const [matchAcceptTimer, setMatchAcceptTimer] = useState(30); // 30 second countdown timer
  const [showAcceptButton, setShowAcceptButton] = useState(true);
  const [playerAcceptances, setPlayerAcceptances] = useState(Array(10).fill(false)); // Track which players have accepted


  // Use WebSocket context
  const { 
    playerData, 
    api, 
    on, 
    reconnect, 
    connected, 
    systemStatus, 
    matchStateInfo, 
    checkQueueEligibility,
    lobbyData 
  } = useWebSocket();

  // Monitor WebSocket connection and reconnect if needed
  useEffect(() => {
    if (!connected) {
      console.log('WebSocket disconnected, attempting to reconnect...');
      reconnect();
    }
  }, [connected, reconnect]);

  // Check queue eligibility when component mounts or lobby changes
  useEffect(() => {
    if (connected && lobbyData?.id) {
      console.log('🔍 Checking queue eligibility for lobby:', lobbyData.id);
      checkQueueEligibility(lobbyData.id);
    }
  }, [connected, lobbyData?.id, checkQueueEligibility]);

  // Set default region and servers (will be overridden by user selection)
  useEffect(() => {
    setPlayerRegion('na');
    setAvailableServers(['Virginia', 'Illinois', 'Georgia', 'California', 'Dallas', 'Oregon']);
  }, []);

  // Available maps for Valorant
  const availableMaps = [
    'Ascent', 'Bind', 'Breeze', 'Fracture', 'Haven', 'Icebox', 'Lotus', 'Pearl', 'Split','Sunset','Corrode','Abyss'
  ];

  // Available servers (will be populated based on detected region)
  const [availableServers, setAvailableServers] = useState([]);
  const [playerRegion, setPlayerRegion] = useState(null);


  // Initialize with current player
  useEffect(() => {
    if (playerData && players.length === 0) {
      setPlayers([{
        puuid: playerData.puuid,
        alias: playerData.alias,
        rank: playerData.rank,
        elo: playerData.elo,
        isLeader: true
      }]);
    }
  }, [playerData]);

  // Auto-scroll chat
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages]);

  // Listen for queue events
  useEffect(() => {
    const unsubscribeQueueJoined = on('queue_joined', (payload) => {
      setQueueStatus({
        in_queue: true,
        queue_type: payload.queue_type,
        estimated_wait: payload.estimated_wait,
        players_in_queue: payload.players_in_queue || 0
      });
      // Set queue start time if not already set
      if (!queueStartTime) {
        setQueueStartTime(Date.now());
      }
    });

    const unsubscribeQueueLeft = on('queue_left', () => {
      setQueueStatus({
        in_queue: false,
        queue_type: null,
        estimated_wait: 0,
        players_in_queue: 0
      });
      setQueueStartTime(null); // Reset timer when leaving queue
    });

    const unsubscribeMatchFound = on('pug_match_found', (payload) => {
      console.log('🎮 [DEBUG] pug_match_found event received:', payload);
      setMatchFound(true);
      setMatchData(payload);
      setTimeLeft(payload.accept_deadline || 30);
      setAcceptedCount(0);
      setTotalPlayers(10);
      setUserAccepted(false);
    });

    const unsubscribePlayerAccepted = on('player_accepted', (payload) => {
      console.log('🔔 [DEBUG] player_accepted event received:', payload);
      console.log('🔔 [DEBUG] Setting acceptedCount to:', payload.accepted_count || 0);
      console.log('🔔 [DEBUG] Setting totalPlayers to:', payload.total_players || 10);
      console.log('🔔 [DEBUG] Server timeout_seconds:', payload.timeout_seconds);
      setAcceptedCount(payload.accepted_count || 0);
      setTotalPlayers(payload.total_players || 10);
      
      // Sync with server time if there's a significant discrepancy (>2 seconds)
      // This handles clock drift while keeping the countdown smooth
      const serverTime = payload.timeout_seconds || 30;
      setTimeLeft(prev => {
        const diff = Math.abs(prev - serverTime);
        if (diff > 2) {
          console.log(`⏰ Syncing timer: ${prev}s -> ${serverTime}s (diff: ${diff}s)`);
          return serverTime;
        }
        return prev; // Keep local countdown if close enough
      });
    });

    const unsubscribeMatchReady = on('match_ready', (payload) => {
      // All players accepted - match ready (legacy event)
      setMatchFound(false);
      console.log('Match ready!', payload);
    });
    
    const unsubscribeMatchConfirmed = on('match_confirmed', (payload) => {
      // All players accepted - redirect to match page
      console.log('Match confirmed! Redirecting to match page...', payload);
      setMatchFound(false);
      
      // Auto-redirect to match page
      if (payload.match_id) {
        navigate(`/match/${payload.match_id}`);
      }
    });

    const unsubscribeMatchTimeout = on('match_timeout', (payload) => {
      // Match acceptance timed out - close modal
      console.log('Match acceptance timed out:', payload);
      
      // Check if user accepted before timing out
      const userDidAccept = userAccepted;
      
      setMatchFound(false);
      setMatchData(null);
      setAcceptedCount(0);
      setTotalPlayers(10);
      setUserAccepted(false);
      
      // Only remove from queue if user DIDN'T accept
      // If user accepted, they should be requeued automatically by the server
      if (!userDidAccept && queueStatus.in_queue) {
        console.log('User did not accept - leaving queue');
        api.leavePugQueue();
        setQueueStartTime(null);
      } else if (userDidAccept) {
        console.log('User accepted - staying in queue for automatic requeue');
      }
    });

    const unsubscribeLobbyMessage = on('lobby_message', (payload) => {
      setChatMessages(prev => [...prev, payload]);
    });

    // ============================================
    // MATCH FOUND BANNER - WebSocket event listener
    // ============================================
    const unsubscribeMatchFoundBanner = on('match_found_banner', (payload) => {
      console.log('🎯 [BANNER] Match found banner event received:', payload);
      setShowMatchBanner(true);
      setMatchBannerData({
        map: payload.map || 'Unknown Map',
        match_id: payload.match_id,
        server: payload.server
      });
      // Reset acceptance tracking when new match is found
      setPlayerAcceptances(Array(10).fill(false));
      setShowAcceptButton(true);
      setMatchAcceptTimer(30);
    });

    // WebSocket listener: Player accepted match
    const unsubscribePlayerAcceptedMatch = on('player_accepted_match', (payload) => {
      console.log('✅ [BANNER] Player accepted match:', payload);
      // payload: { player_index: number, accepted_count: number, total_players: number }
      if (payload.player_index !== undefined && payload.player_index >= 0 && payload.player_index < 10) {
        setPlayerAcceptances(prev => {
          const newAcceptances = [...prev];
          newAcceptances[payload.player_index] = true;
          return newAcceptances;
        });
      }
    });

    // ============================================
    // INVITE EVENT LISTENERS - Full WebSocket implementation
    // ============================================
    const unsubscribeInviteSent = on('invite_sent', (payload) => {
      console.log('✅ Invite sent successfully:', payload);
      setInvitingPlayer(null);
      setInviteError(null);
      
      // Show success notification
      if (window.showNotification) {
        window.showNotification({
          type: 'success',
          title: 'Invite Sent',
          message: `Invite sent to ${payload.target_player?.alias || 'player'}`,
          duration: 3000
        });
      }
    });

    const unsubscribeInviteAccepted = on('invite_accepted', (payload) => {
      console.log('🎉 Player accepted invite:', payload);
      
      // Add player to local players state
      if (payload.player_data) {
        setPlayers(prev => {
          // Check if player already exists to avoid duplicates
          const exists = prev.some(p => p.puuid === payload.player_data.puuid);
          if (exists) return prev;
          
          return [...prev, {
            puuid: payload.player_data.puuid,
            alias: payload.player_data.alias,
            rank: payload.player_data.rank,
            elo: payload.player_data.elo,
            isLeader: false
          }];
        });
      }
      
      // Close invite dialog
      setInviteDialogOpen(false);
      
      // Show success notification
      if (window.showNotification) {
        window.showNotification({
          type: 'success',
          title: 'Player Joined',
          message: `${payload.player_data?.alias || 'Player'} joined the lobby!`,
          duration: 4000
        });
      }
    });

    const unsubscribeInviteDeclined = on('invite_declined', (payload) => {
      console.log('❌ Player declined invite:', payload);
      
      // Show notification that player declined
      if (window.showNotification) {
        window.showNotification({
          type: 'info',
          title: 'Invite Declined',
          message: `${payload.player_alias || 'Player'} declined the invitation`,
          duration: 4000
        });
      }
    });

    const unsubscribeInviteExpired = on('invite_expired', (payload) => {
      console.log('⏰ Invite expired:', payload);
      setInvitingPlayer(null);
      
      // Show notification about expired invite
      if (window.showNotification) {
        window.showNotification({
          type: 'warning',
          title: 'Invite Expired',
          message: 'The player did not respond in time',
          duration: 4000
        });
      }
    });

    const unsubscribeLobbyFull = on('lobby_full', (payload) => {
      console.log('⚠️ Lobby is full:', payload);
      setInviteDialogOpen(false);
      
      // Show notification
      if (window.showNotification) {
        window.showNotification({
          type: 'warning',
          title: 'Lobby Full',
          message: 'The lobby is already full',
          duration: 3000
        });
      }
    });

    const unsubscribeAvailablePlayers = on('available_players_list', (payload) => {
      console.log('📋 Received available players:', payload);
      setAvailablePlayers(payload.players || []);
      setLoadingPlayers(false);
    });

    const unsubscribeInviteError = on('invite_error', (payload) => {
      console.error('❌ Invite error:', payload);
      setInvitingPlayer(null);
      setInviteError(payload.message);
      
      // Error message mapping
      const errorMessages = {
        'player_offline': 'Player is currently offline',
        'player_in_match': 'Player is in an active match',
        'lobby_full': 'Lobby is already full',
        'permission_denied': 'You do not have permission to invite players',
        'player_not_found': 'Player not found',
        'already_in_lobby': 'Player is already in a lobby'
      };
      
      // Show error notification
      if (window.showNotification) {
        window.showNotification({
          type: 'error',
          title: 'Invite Failed',
          message: errorMessages[payload.error_code] || payload.message || 'Failed to send invite',
          duration: 5000
        });
      }
    });

    const unsubscribePlayerStatusUpdate = on('player_status_changed', (payload) => {
      console.log('🔄 Player status updated:', payload);
      
      // Update player status in available players list
      setAvailablePlayers(prev => prev.map(player =>
        player.puuid === payload.puuid
          ? { ...player, status: payload.status }
          : player
      ));
    });

    return () => {
      if (typeof unsubscribeQueueJoined === 'function') unsubscribeQueueJoined();
      if (typeof unsubscribeQueueLeft === 'function') unsubscribeQueueLeft();
      if (typeof unsubscribeMatchFound === 'function') unsubscribeMatchFound();
      if (typeof unsubscribePlayerAccepted === 'function') unsubscribePlayerAccepted();
      if (typeof unsubscribeMatchReady === 'function') unsubscribeMatchReady();
      if (typeof unsubscribeMatchConfirmed === 'function') unsubscribeMatchConfirmed();
      if (typeof unsubscribeMatchTimeout === 'function') unsubscribeMatchTimeout();
      if (typeof unsubscribeLobbyMessage === 'function') unsubscribeLobbyMessage();
      if (typeof unsubscribeMatchFoundBanner === 'function') unsubscribeMatchFoundBanner();
      // Cleanup invite event listeners
      if (typeof unsubscribeInviteSent === 'function') unsubscribeInviteSent();
      if (typeof unsubscribeInviteAccepted === 'function') unsubscribeInviteAccepted();
      if (typeof unsubscribeInviteDeclined === 'function') unsubscribeInviteDeclined();
      if (typeof unsubscribeInviteExpired === 'function') unsubscribeInviteExpired();
      if (typeof unsubscribeLobbyFull === 'function') unsubscribeLobbyFull();
      if (typeof unsubscribeAvailablePlayers === 'function') unsubscribeAvailablePlayers();
      if (typeof unsubscribeInviteError === 'function') unsubscribeInviteError();
      if (typeof unsubscribePlayerStatusUpdate === 'function') unsubscribePlayerStatusUpdate();
    };
  }, [on]);

  // Countdown timer for match acceptance
  useEffect(() => {
    if (matchFound && timeLeft > 0) {
      const timer = setTimeout(() => {
        setTimeLeft(prev => prev - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (matchFound && timeLeft === 0) {
      // Timer expired - check if user accepted before removing from queue
      console.log('Match acceptance timer expired, closing modal');
      
      // Check if user accepted before timing out
      const userDidAccept = userAccepted;
      
      setMatchFound(false);
      setMatchData(null);
      setAcceptedCount(0);
      setTotalPlayers(10);
      setUserAccepted(false);
      
      // Only remove from queue if user DIDN'T accept
      // If user accepted, they should be requeued automatically by the server
      if (!userDidAccept && queueStatus.in_queue) {
        console.log('User did not accept - leaving queue');
        api.leavePugQueue();
        setQueueStartTime(null);
      } else if (userDidAccept) {
        console.log('User accepted - staying in queue, waiting for server requeue');
        // Don't reset queueStartTime - keep timer running
      }
      
      // Optional: Show a brief message that the match expired
      // You could add a toast notification here if desired
    }
  }, [matchFound, timeLeft]);

  const handleJoinQueue = () => {
    if (selectedMaps.length < 5) {
      return; // Should be disabled by UI
    }
    api.joinPugQueue({
      queue_type: selectedQueueType,
      preferred_maps: selectedMaps,
        preferred_servers: selectedServers
    });
  };

  const handleLeaveQueue = () => {
    api.leavePugQueue();
    setQueueStartTime(null);
  };

  const handleFindMatch = () => {
    if (queueStatus.in_queue) {
      handleLeaveQueue();
    } else {
      // Pre-flight validation check
      if (!matchStateInfo.canQueue) {
        console.warn('❌ Cannot queue - player in active match:', matchStateInfo);
        
        // Show notification to user
        if (window.showNotification) {
          window.showNotification({
            type: 'warning',
            title: 'Cannot Queue',
            message: matchStateInfo.blockedReason || 'You are currently in an active match',
            action: matchStateInfo.matchId ? {
              label: 'Go to Match',
              onClick: () => window.location.href = `/match/${matchStateInfo.matchId}`
            } : null
          });
        }
        return;
      }

      // Double-check eligibility before queuing
      if (connected && lobbyData?.id) {
        checkQueueEligibility(lobbyData.id);
        
        // Wait a moment for validation response, then proceed
        setTimeout(() => {
          if (matchStateInfo.canQueue) {
            // Enter queue
            setQueueStartTime(Date.now());
            api.joinPugQueue({
              queue_type: selectedQueueType,
              preferred_maps: selectedMaps,
              preferred_servers: selectedServers
            });
          }
        }, 100);
      } else {
        // Fallback - proceed without validation if no lobby data
        setQueueStartTime(Date.now());
        api.joinPugQueue({
          queue_type: selectedQueueType,
          preferred_maps: selectedMaps,
          preferred_servers: selectedServers
        });
      }
    }
  };

  // Calculate queue time
  const getQueueTime = () => {
    if (!queueStartTime) return '0:00';
    const elapsed = Math.floor((Date.now() - queueStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // Format region and queue type for title
  const getQueueTitle = () => {
    const queueType = selectedQueueType === 'pug' ? '5v5' : '5v5 Super';
    
    console.log('getQueueTitle - playerRegion:', playerRegion);
    
    if (playerRegion) {
      // Map region codes to display names
      const regionNames = {
        'na': 'North America',
        'eu': 'Europe',
        'latam': 'Latin America',
        'br': 'Brazil',
        'ap': 'Asia Pacific',
        'kr': 'Korea'
      };
      
      const regionName = regionNames[playerRegion] || 'Global';
      const title = `${regionName} ${queueType}`;
      console.log('Generated title:', title);
      return title;
    }
    
    console.log('No playerRegion, using Global');
    return `Global ${queueType}`;
  };

  // Check if current user is party leader
  const isPartyLeader = () => {
    return players.length > 0 && players[0]?.isLeader;
  };

  // Update queue timer every second when in queue
  const [, forceUpdate] = useState(0);
  useEffect(() => {
    let interval;
    if (queueStatus.in_queue && queueStartTime) {
      interval = setInterval(() => {
        // Force re-render to update timer display
        forceUpdate(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [queueStatus.in_queue, queueStartTime]);

  const sendLobbyMessage = () => {
    if (!newMessage.trim()) return;
    
    const message = {
      user: playerData?.alias || 'Unknown',
      message: newMessage.trim(),
      timestamp: new Date().toISOString(),
      type: 'lobby'
    };
    
    setChatMessages(prev => [...prev, message]);
    setNewMessage('');
  };

  // ============================================
  // INVITE DIALOG HANDLERS - Open dialog and manage invitations
  // ============================================
  const handleEmptySlotClick = (slotIndex) => {
    console.log('Empty slot clicked:', slotIndex);
    setInviteDialogOpen(true);
    setSearchQuery('');
    setInviteError(null);
    setLoadingPlayers(true);
    
    // Fetch available players via WebSocket

    /*
    if (api.getAvailablePlayers) {
      api.getAvailablePlayers({
        status: 'online',
        exclude_lobby_members: true,
        lobby_id: lobbyData?.id
      });
    } else {
      console.warn('getAvailablePlayers API method not available');
      setLoadingPlayers(false);
    }*/

      setTimeout(() => {
      setAvailablePlayers([
        { puuid: '1', alias: 'Player1', rank: 'Immortal 2', elo: 1850, status: 'online' },
        { puuid: '2', alias: 'Player2', rank: 'Platinum 3', elo: 1650, status: 'online' },
        { puuid: '3', alias: 'Player3', rank: 'Diamond 1', elo: 1800, status: 'in_game' },
        { puuid: '4', alias: 'Player4', rank: 'Ascendant 1', elo: 1950, status: 'online' },
        { puuid: '5', alias: 'Player5', rank: 'Gold 3', elo: 1450, status: 'online' },
        { puuid: '6', alias: 'TestUser123', rank: 'Radiant', elo: 1550, status: 'online' },
        { puuid: '7', alias: 'Ayprusss', rank: 'Silver 2', elo: 1300, status: 'offline'},
        { puuid: '8', alias: 'beeprusss', rank: 'bronze 1', elo: 950, status: 'offline'},
        {puuid: '9', alias: 'ceepruss', rank: 'iron 3', elo: 550, status:'online'},
        {puuid: '10', alias: 'bich nga cafe', rank: 'unranked', elo: 0, status:'online'}
      ]);
      setLoadingPlayers(false);
    }, 500); // Simulate network delay
  };

  const handleInvitePlayer = (playerPuuid, playerAlias) => {
    console.log('Inviting player:', playerPuuid, playerAlias);
    setInvitingPlayer(playerPuuid);
    setInviteError(null);
    
    // Validate lobby data
    if (!lobbyData?.id) {
      console.error('Cannot invite: No active lobby');
      setInvitingPlayer(null);
      setInviteError('No active lobby found');
      
      if (window.showNotification) {
        window.showNotification({
          type: 'error',
          title: 'Cannot Invite',
          message: 'No active lobby found',
          duration: 3000
        });
      }
      return;
    }
    
    // Send invite via WebSocket
    if (api.sendLobbyInvite) {
      api.sendLobbyInvite(lobbyData.id, playerPuuid);
    } else {
      console.error('sendLobbyInvite API method not available');
      setInvitingPlayer(null);
      setInviteError('Invite feature not available');
      
      if (window.showNotification) {
        window.showNotification({
          type: 'error',
          title: 'Cannot Invite',
          message: 'Invite feature is not available',
          duration: 3000
        });
      }
    }
  };

  const handleCloseInviteDialog = () => {
    setInviteDialogOpen(false);
    setSearchQuery('');
    setInvitingPlayer(null);
  };

  // Refresh available players when WebSocket reconnects while dialog is open
  useEffect(() => {
    if (connected && inviteDialogOpen && api.getAvailablePlayers) {
      console.log('🔄 WebSocket reconnected - refreshing available players');
      setLoadingPlayers(true);
      api.getAvailablePlayers({
        status: 'online',
        exclude_lobby_members: true,
        lobby_id: lobbyData?.id
      });
    }
  }, [connected, inviteDialogOpen]);

  // Match Accept Timer - Countdown from 30 seconds
  useEffect(() => {
    if (!showMatchBanner || matchAcceptTimer <= 0) return;

    const timerInterval = setInterval(() => {
      setMatchAcceptTimer(prev => {
        if (prev <= 1) {
          // Timer expired - auto-close banner
          setShowMatchBanner(false);
          setMatchAcceptTimer(30); // Reset timer
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timerInterval);
  }, [showMatchBanner, matchAcceptTimer]);


  // Filter players based on search query
  const filteredPlayers = availablePlayers.filter(player =>
    player.alias.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleAcceptMatch = () => {
    setShowAcceptButton(false);
    if (matchData?.match_id) {
      api.acceptMatch(matchData.match_id);
      setUserAccepted(true); // Mark that user has accepted
    }
    // Don't close modal yet - wait for server response
  };

  const handleDeclineMatch = () => {
    if (matchData?.match_id) {
      api.declineMatch(matchData.match_id);
    }
    setMatchFound(false);
    setMatchData(null);
    setAcceptedCount(0);
    setTotalPlayers(10);
    setUserAccepted(false);
    
    // Remove user from queue since they declined the match
    if (queueStatus.in_queue) {
      api.leavePugQueue();
      setQueueStartTime(null);
    }
  };

  const toggleMap = (mapName) => {
    setSelectedMaps(prev => 
      prev.includes(mapName) 
        ? prev.filter(m => m !== mapName)
        : [...prev, mapName]
    );
  };

  const toggleServer = (serverName) => {
    setSelectedServers(prev => 
      prev.includes(serverName) 
        ? prev.filter(s => s !== serverName)
        : [...prev, serverName]
    );
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Component for showing acceptance progress
  const AcceptanceProgress = () => {
    console.log('[DEBUG] AcceptanceProgress render - acceptedCount:', acceptedCount, 'totalPlayers:', totalPlayers);
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 0.5, mb: 2 }}>
        {Array.from({ length: totalPlayers }).map((_, index) => (
          <Box
            key={index}
            sx={{
              width: '20px',
              height: '20px',
              borderRadius: '50%',
              backgroundColor: index < acceptedCount ? theme.palette.secondary.main : '#333',
              border: `2px solid ${index < acceptedCount ? theme.palette.secondary.main : '#555'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.3s ease'
            }}
          >
            <Typography
              sx={{
                fontSize: '10px',
                color: index < acceptedCount ? '#000' : '#999',
                fontWeight: 'bold'
              }}
            >
              {index < acceptedCount ? '✓' : '○'}
            </Typography>
          </Box>
        ))}
      </Box>
    );
  };
  

  return (
    <Container maxWidth="md" sx={{ height: '100%', overflow: 'hidden' }}>
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          backgroundColor: theme.palette.background.dark,
          padding: `${theme.spacing(1)} 0 ${theme.spacing(2)} 0`,
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        {/* Match Found Banner with Overlay */}
        {showMatchBanner && (
          <>
            {/* Gray Overlay Background */}
            <Box
              sx={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                zIndex: 9998,
                backdropFilter: 'blur(4px)',
              }}
              onClick={(e) => e.stopPropagation()} // Prevent clicks from going through
            />
            
            {/* Match Found Banner */}
            <Box
              sx={{
                position: 'fixed',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                zIndex: 9999,
                width: '90%',
                maxWidth: '500px',
              }}
            >
              <Paper
                elevation={24}
                sx={{
                  position: 'relative',
                  backgroundColor: theme.palette.background.paper,
                  border: `3px solid ${theme.palette.secondary.main}`,
                  borderRadius: '12px',
                  padding: theme.spacing(4),
                  textAlign: 'center',
                  boxShadow: `0 0 40px ${theme.palette.secondary.main}80`,
                  overflow: 'hidden',
                  // Background image setup
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    backgroundImage: `url(/maps/${matchBannerData.map?.toLowerCase().replace(/\s+/g, '')}.jpg)`,
                    backgroundSize: 'cover',
                    backgroundPosition: 'center',
                    opacity: 0.2,
                    zIndex: 0,
                  }
                }}
              >
                {/* Content wrapper with relative positioning */}
                <Box sx={{ position: 'relative', zIndex: 1 }}>
                  {/* Header */}
                  <Typography
                    variant="h2"
                    sx={{
                      color: theme.palette.secondary.main,
                      fontWeight: 'bold',
                      textTransform: 'uppercase',
                      letterSpacing: '3px',
                      mb: 2,
                      textShadow: `0 0 20px ${theme.palette.secondary.main}60`,
                    }}
                  >
                    MATCH FOUND
                  </Typography>
                  
                  {/* Subheader - Map Name */}
                  <Typography
                    variant="h5"
                    sx={{
                      color: theme.palette.text.primary,
                      fontWeight: 500,
                      mb: 3,
                    }}
                  >
                    {matchBannerData.map || 'Unknown Map'}
                  </Typography>
                  
                  {/* Timer Display */}
                  <Box
                    sx={{
                      mb: 3,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: 1,
                    }}
                  >
                    <Typography
                      variant="h3"
                      sx={{
                        color: matchAcceptTimer <= 10 
                          ? theme.palette.error.main 
                          : theme.palette.success.main,
                        fontWeight: 'bold',
                        fontSize: '2rem',
                      }}
                    >
                      {matchAcceptTimer}
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{
                        color: theme.palette.text.secondary,
                        textTransform: 'uppercase',
                        letterSpacing: '1px',
                      }}
                    >
                      Accept within time limit
                    </Typography>
                  </Box>
                  
                  {/*User list Showing Number of Players Accepting Match*/}
                  {!showAcceptButton && (
                    <Box
                      sx={{
                        mb: 3,
                        display: 'flex',
                        flexDirection: 'row',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 1.5,
                        flexWrap: 'wrap',
                      }}
                    >
                      {Array.from({length: 10}).map((_, index) => (
                        <Person
                          key={index}
                          sx={{
                            fontSize: '2rem',
                            color: playerAcceptances[index] 
                              ? theme.palette.common.white 
                              : theme.palette.action.disabled,
                            transition: 'all 0.3s ease',
                            filter: playerAcceptances[index] 
                              ? 'drop-shadow(0 0 8px rgba(255, 255, 255, 0.8))' 
                              : 'none',
                          }}
                        />
                      ))}
                    </Box>
                  )}
                  {/* Accept Match Button */}
                  {showAcceptButton && (
                    <Button
                      variant="contained"
                      onClick={() => {
                        // Send WebSocket event to notify server of acceptance
                        if (matchBannerData.match_id) {
                          api.emit('accept_match', {
                            match_id: matchBannerData.match_id,
                          });
                        }
                        
                        // Hide the accept button and show the acceptance tracker
                        setShowAcceptButton(false);
                        
                        // Mark current user as accepted (assume player index 0 for now, server will broadcast actual index)
                        setPlayerAcceptances(prev => {
                          const newAcceptances = [...prev];
                          newAcceptances[0] = true; // This will be overridden by server broadcast
                          return newAcceptances;
                        });
                      }}
                      sx={{
                        backgroundColor: theme.palette.success.main,
                        color: theme.palette.getContrastText(theme.palette.success.main),
                        fontWeight: 'bold',
                        fontSize: '1.1rem',
                        px: 6,
                        py: 1.5,
                        textTransform: 'uppercase',
                        letterSpacing: '2px',
                        '&:hover': {
                          backgroundColor: theme.palette.success.dark,
                        },
                      }}
                    >
                      ACCEPT
                    </Button>
                    )}
                </Box>
              </Paper>
            </Box>
          </>
        )}

        {/* Header */}
        <Typography variant="h4" align="center" gutterBottom sx={{ color: theme.palette.secondary.main }}>
          {getQueueTitle()}
        </Typography>
        

        
        
        {/* Player Cards Section */}
        <Grid container spacing={1.5} justifyContent="center" alignItems="center" sx={{ mt: -2, mb: 0, minHeight: '200px' }}>
          {Array.from({ length: 5 }).map((_, index) => {
            // Center the user's player card (index 2)
            let player = null;
            if (index === 2 && players.length > 0) {
              // Put the first player (current user) in the middle slot
              player = players[0];
            } else if (index !== 2 && players.length > index + (index > 2 ? 0 : 1)) {
              // Put other players in remaining slots
              const playerIndex = index > 2 ? index : index + 1;
              player = players[playerIndex];
            }
            
            return (
              <Grid item key={player ? player.puuid : `empty-${index}`} xs={2.4}>
                <PlayerSlot 
                  player={player} 
                  handleEmptySlotClick={handleEmptySlotClick} 
                  slotIndex={index} 
                />
              </Grid>
            );
          })}
        </Grid>


        {/* Horizontal Settings Card */}
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between', 
          mt: 4,
          mb: 0,
          px: 1.5,
          py: 1,
          backgroundColor: theme.palette.background.paper,
          borderRadius: 1,
        }}>
          {/* Left side - Toggle tabs */}
          <Box sx={{ display: 'flex', flex: 1, gap: 2 }}>
            <Button
              variant={activeTab === 'match_type' ? 'contained' : 'text'}
              onClick={() => setActiveTab('match_type')}
              size="small"
              sx={{
                color: activeTab === 'match_type' ? 'white' : theme.palette.text.secondary,
                borderBottom: activeTab === 'match_type' ? `2px solid ${theme.palette.secondary.main}` : 'none',
                borderRadius: 0,
                px: 1.5,
                py: 0.5,
                fontSize: '0.875rem',
                minHeight: 'auto',
              }}
            >
              MATCH TYPE
            </Button>
            <Button
              variant={activeTab === 'maps' ? 'contained' : 'text'}
              onClick={() => setActiveTab('maps')}
              size="small"
              sx={{
                color: activeTab === 'maps' ? 'white' : theme.palette.text.secondary,
                borderBottom: activeTab === 'maps' ? `2px solid ${theme.palette.secondary.main}` : 'none',
                borderRadius: 0,
                px: 1.5,
                py: 0.5,
                fontSize: '0.875rem',
                minHeight: 'auto',
              }}
            >
              MAPS {selectedMaps.length}/9
            </Button>
            <Button
              variant={activeTab === 'servers' ? 'contained' : 'text'}
              onClick={() => setActiveTab('servers')}
              size="small"
              sx={{
                color: activeTab === 'servers' ? 'white' : theme.palette.text.secondary,
                borderBottom: activeTab === 'servers' ? `2px solid ${theme.palette.secondary.main}` : 'none',
                borderRadius: 0,
                px: 1.5,
                py: 0.5,
                fontSize: '0.875rem',
                minHeight: 'auto',
              }}
            >
              SERVERS {selectedServers.length}/{availableServers.length}
            </Button>
          </Box>

          {/* Right side - Find Match Button */}
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
            {/* Match State Indicator */}
            {matchStateInfo.inActiveMatch && (
              <Box sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                px: 2,
                py: 0.5,
                backgroundColor: theme.palette.warning.main,
                borderRadius: 1,
                fontSize: '0.75rem',
                color: theme.palette.getContrastText(theme.palette.warning.main)
              }}>
                <Box sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: theme.palette.getContrastText(theme.palette.warning.main),
                  animation: 'pulse 2s infinite'
                }} />
                <Typography variant="caption" sx={{ fontWeight: 600 }}>
                  {matchStateInfo.matchState ? 
                    `${matchStateInfo.matchState.replace('_', ' ').toUpperCase()} MATCH` : 
                    'ACTIVE MATCH'
                  }
                </Typography>
                {matchStateInfo.matchId && (
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => window.location.href = `/match/${matchStateInfo.matchId}`}
                    sx={{
                      fontSize: '0.6rem',
                      py: 0.25,
                      px: 1,
                      minHeight: 'auto',
                      borderColor: theme.palette.getContrastText(theme.palette.warning.main),
                      color: theme.palette.getContrastText(theme.palette.warning.main),
                      '&:hover': {
                        backgroundColor: 'rgba(255,255,255,0.1)'
                      }
                    }}
                  >
                    GO TO MATCH
                  </Button>
                )}
              </Box>
            )}
            <Button
              variant="contained"
              size="medium"
              onClick={handleFindMatch}
              disabled={
                selectedMaps.length < 5 || 
                !isPartyLeader() || 
                !connected || 
                systemStatus.valorant.status !== 'running' ||
                (!queueStatus.in_queue && !matchStateInfo.canQueue)
              }
              sx={{
                fontSize: '1rem',
                py: 0.75, 
                px: 4, 
                minWidth: '140px', // Fixed width to prevent growing
                backgroundColor: 
                  !matchStateInfo.canQueue && !queueStatus.in_queue ? theme.palette.warning.main :
                  queueStatus.in_queue ? theme.palette.error.main : 
                  theme.palette.secondary.main,
                color: theme.palette.getContrastText(
                  !matchStateInfo.canQueue && !queueStatus.in_queue ? theme.palette.warning.main :
                  queueStatus.in_queue ? theme.palette.error.main : 
                  theme.palette.secondary.main
                ),
                '&:hover': {
                  backgroundColor: 
                    !matchStateInfo.canQueue && !queueStatus.in_queue ? theme.palette.warning.dark :
                    queueStatus.in_queue ? theme.palette.error.dark : 
                    theme.palette.secondary.dark,
                },
                '&:disabled': {
                  backgroundColor: theme.palette.action.disabled,
                }
              }}
            >
              {
                !matchStateInfo.canQueue && !queueStatus.in_queue ? 'IN ACTIVE MATCH' :
                queueStatus.in_queue ? `CANCEL (${getQueueTime()})` : 
                'FIND MATCH'
              }
            </Button>
          </Box>
        </Box>

        {/* Tab Content */}
        <Box sx={{ mb: 3, minHeight: 'auto', backgroundColor: theme.palette.background.paper, borderRadius: 1, px: 1.5, pt: 1, pb: 1, mt: 0 }}>
          {activeTab === 'match_type' && (
            <Box>
              <Grid container spacing={1.5}>
                <Grid item xs={6}>
                  <Card
                    sx={{
                      cursor: 'pointer',
                      border: selectedQueueType === 'pug' ? `2px solid ${theme.palette.secondary.main}` : '1px solid transparent',
                      backgroundColor: selectedQueueType === 'pug' ? theme.palette.action.hover : 'transparent',
                      '&:hover': { backgroundColor: theme.palette.action.hover },
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column'
                    }}
                    onClick={() => setSelectedQueueType('pug')}
                  >
                    <CardContent sx={{ p: 1, pb: 0.5, display: 'flex', flexDirection: 'column', height: '100%' }}>
                      <Typography variant="h6" gutterBottom>
                        5v5 Match
                      </Typography>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          A competitive experience, with fast balanced matches.
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6}>
                  <Card
                    sx={{
                      cursor: 'pointer',
                      border: selectedQueueType === 'scrim' ? `2px solid ${theme.palette.secondary.main}` : '1px solid transparent',
                      backgroundColor: selectedQueueType === 'scrim' ? theme.palette.action.hover : 'transparent',
                      '&:hover': { backgroundColor: theme.palette.action.hover },
                      opacity: 0.6,
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column'
                    }}
                    onClick={() => {/* setSelectedQueueType('scrim') */}}
                  >
                    <CardContent sx={{ p: 1, pb: 0.5, display: 'flex', flexDirection: 'column', height: '100%' }}>
                      <Typography variant="h6" gutterBottom>
                        5v5 Super Match
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexGrow: 1 }}>
                        <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1, maxWidth: '70%' }}>
                          Solo, duo, trio only • 400 Elo range • Veteran matching • Vote kick • Premium matching
                        </Typography>
                        <Button variant="contained" color="success" size="small">
                          UPGRADE
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Box>
          )}

          {activeTab === 'maps' && (
            <Box>
              <Grid container spacing={0.25}>
                {availableMaps.map((map) => (
                  <Grid item xs={3} sm={2.4} md={1.8} key={map}>
                    <Card
                      sx={{
                        cursor: 'pointer',
                        border: selectedMaps.includes(map) ? `2px solid ${theme.palette.secondary.main}` : '1px solid transparent',
                        backgroundColor: selectedMaps.includes(map) ? theme.palette.action.hover : 'transparent',
                        '&:hover': { backgroundColor: theme.palette.action.hover }
                      }}
                      onClick={() => toggleMap(map)}
                    >
                      <CardContent sx={{ p: 0.5, '&:last-child': { pb: 0.5 }, textAlign: 'center' }}>
                        <Typography variant="caption" sx={{ fontSize: '0.75rem', textAlign: 'center' }}>
                          {map}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
              <Typography variant="caption" color={selectedMaps.length < 5 ? "error" : "text.secondary"} sx={{ mt: 1, mb: 0, display: 'block' }}>
                {selectedMaps.length < 5 ? `Select at least 5 maps to queue (${5 - selectedMaps.length} more needed)` : 'Map selection complete'}
              </Typography>
            </Box>
          )}

          {activeTab === 'servers' && (
            <Box>
              <Grid container spacing={0.25}>
                {availableServers.map((server) => (
                  <Grid item xs={3} sm={2.4} md={1.8} key={server}>
                    <Card
                      sx={{
                        cursor: 'pointer',
                        border: selectedServers.includes(server) ? `2px solid ${theme.palette.secondary.main}` : '1px solid transparent',
                        backgroundColor: selectedServers.includes(server) ? theme.palette.action.hover : 'transparent',
                        '&:hover': { backgroundColor: theme.palette.action.hover }
                      }}
                      onClick={() => toggleServer(server)}
                    >
                      <CardContent sx={{ p: 0.5, '&:last-child': { pb: 0.5 }, textAlign: 'center' }}>
                        <Typography variant="caption" sx={{ fontSize: '0.75rem', textAlign: 'center' }}>
                          {server.charAt(0).toUpperCase() + server.slice(1)}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, mb: 0, display: 'block' }}>
                Select preferred servers. Leave empty to allow all servers.
              </Typography>
            </Box>
          )}
        </Box>
        
        {/* Minimal spacer to control gap above chatbox */}
        <Box sx={{ height: '1px' }} />
        
        {/* Chatbox Section - Fixed height to prevent expansion */}
        <Box sx={{ 
          position: 'absolute',
          bottom: theme.spacing(2),
          left: theme.spacing(0.5),
          right: theme.spacing(0.5),
          height: '24vh',
          display: 'flex', 
          flexDirection: 'column', 
          border: '1px solid grey', 
          borderRadius: '8px', 
          overflow: 'hidden',
          backgroundColor: theme.palette.background.paper
        }}>
          {/* Messages List */}
          <List sx={{ flexGrow: 1, overflowY: 'auto', p: 1 }}>
            {chatMessages.map((message, index) => (
              <ListItem key={index} sx={{ py: 0.1, minHeight: 'auto' }}>
                <ListItemText
                  primary={
                    <Typography variant="body2" sx={{ lineHeight: 1.2 }}>
                      [{new Date(message.timestamp).toLocaleTimeString()}] <strong>{message.user}</strong>: {message.message}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
            <div ref={messagesEndRef} />
          </List>
          
          {/* Message Input */}
          <Box sx={{ display: 'flex', p: 1, borderTop: '1px solid grey' }}>
            <TextField
              variant="outlined"
              fullWidth
              size="small"
              placeholder="Type a message..."
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  sendLobbyMessage();
                }
              }}
            />
            <Button onClick={sendLobbyMessage} sx={{ ml: 1 }} variant="contained">
              Send
            </Button>
          </Box>
        </Box>

        {/* ============================================ */}
        {/* INVITE PLAYER DIALOG - New feature for inviting players to lobby */}
        {/* ============================================ */}
        <Dialog
          open={inviteDialogOpen}
          onClose={handleCloseInviteDialog}
          maxWidth="sm"
          fullWidth
          PaperProps={{
            sx: {
              backgroundColor: theme.palette.background.dark,
              border: '2px solid #333',
              borderRadius: '8px',
              boxShadow: '0 8px 32px rgba(0,0,0,0.8)'
            }
          }}
        >
          <DialogTitle sx={{ 
            pb: 1, 
            borderBottom: '1px solid #333',
            color: '#fff'
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <People sx={{ color: theme.palette.secondary.main }} />
                <Typography variant="h6" sx={{ fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '1px' }}>
                  Invite Player
                </Typography>
              </Box>
              <IconButton
                onClick={handleCloseInviteDialog}
                sx={{
                  color: '#888',
                  '&:hover': {
                    color: '#fff',
                    backgroundColor: 'rgba(255,255,255,0.1)'
                  }
                }}
              >
                ✕
              </IconButton>
            </Box>
          </DialogTitle>
          
          <DialogContent sx={{ p: 2 }}>
            {/* Search Bar */}
            <Box sx={{ mb: 2 }}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search players..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: <Search sx={{ mr: 1, color: '#888' }} />,
                  sx: {
                    backgroundColor: '#0f0f0f',
                    borderRadius: '4px',
                    color: '#fff',
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: '#333'
                    },
                    '&:hover .MuiOutlinedInput-notchedOutline': {
                      borderColor: theme.palette.secondary.main
                    },
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                      borderColor: theme.palette.secondary.main
                    }
                  }
                }}
              />
            </Box>

            {/* Error Display */}
            {inviteError && (
              <Box sx={{ mb: 2, p: 1.5, backgroundColor: 'rgba(244, 67, 54, 0.1)', borderRadius: '4px', border: '1px solid rgba(244, 67, 54, 0.3)' }}>
                <Typography variant="body2" sx={{ color: '#f44336' }}>
                  ⚠️ {inviteError}
                </Typography>
              </Box>
            )}

            {/* Player List */}
            <List sx={{ 
              maxHeight: '400px', 
              overflowY: 'auto',
              '&::-webkit-scrollbar': {
                width: '8px'
              },
              '&::-webkit-scrollbar-track': {
                backgroundColor: '#0f0f0f'
              },
              '&::-webkit-scrollbar-thumb': {
                backgroundColor: '#333',
                borderRadius: '4px',
                '&:hover': {
                  backgroundColor: '#444'
                }
              }
            }}>
              {loadingPlayers ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    Loading available players...
                  </Typography>
                </Box>
              ) : filteredPlayers.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    {searchQuery ? 'No players found matching your search' : availablePlayers.length === 0 ? 'No players available to invite' : 'No available players'}
                  </Typography>
                </Box>
              ) : (
                filteredPlayers.map((player) => (
                  <ListItem
                    key={player.puuid}
                    sx={{
                      mb: 1,
                      backgroundColor: '#0f0f0f',
                      borderRadius: '4px',
                      border: '1px solid #222',
                      '&:hover': {
                        backgroundColor: '#1a1a1a',
                        borderColor: theme.palette.secondary.main
                      },
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <ListItemAvatar>
                      <Badge
                        overlap="circular"
                        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                        badgeContent={
                          <Box
                            sx={{
                              width: 12,
                              height: 12,
                              borderRadius: '50%',
                              backgroundColor: player.status === 'online' ? '#4caf50' : '#ff9800',
                              border: '2px solid #1a1a1a'
                            }}
                          />
                        }
                      >
                        <Avatar
                          sx={{
                            width: 48,
                            height: 48,
                            backgroundColor: theme.palette.secondary.main,
                            color: '#000',
                            fontWeight: 'bold'
                          }}
                        >
                          {player.alias.charAt(0).toUpperCase()}
                        </Avatar>
                      </Badge>
                    </ListItemAvatar>
                    
                    <ListItemText
                      primary={
                        <Typography variant="body1" sx={{ color: '#fff', fontWeight: 'bold' }}>
                          {player.alias}
                        </Typography>
                      }
                      secondary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                          <Chip
                            label={player.rank}
                            size="small"
                            sx={{
                              backgroundColor: theme.palette.ranks[player.rank.toLowerCase().split(' ')[0]],
                              color: '#000',
                              fontWeight: 'bold',
                              fontSize: '0.7rem',
                              height: '20px'
                            }}
                          />
                          <Typography variant="caption" sx={{ color: '#888' }}>
                            {player.elo} ELO
                          </Typography>
                          {player.status === 'in_game' && (
                            <Chip
                              label="In Game"
                              size="small"
                              sx={{
                                backgroundColor: '#ff9800',
                                color: '#000',
                                fontSize: '0.65rem',
                                height: '18px'
                              }}
                            />
                          )}
                        </Box>
                      }
                    />
                    
                    <Button
                      variant="contained"
                      size="small"
                      disabled={invitingPlayer === player.puuid || player.status === 'in_game'}
                      onClick={() => handleInvitePlayer(player.puuid, player.alias)}
                      startIcon={invitingPlayer === player.puuid ? null : <Add />}
                      sx={{
                        backgroundColor: theme.palette.secondary.main,
                        color: theme.palette.getContrastText(theme.palette.secondary.main),
                        fontWeight: 'bold',
                        textTransform: 'uppercase',
                        fontSize: '0.75rem',
                        px: 2,
                        '&:hover': {
                          backgroundColor: theme.palette.secondary.dark
                        },
                        '&:disabled': {
                          backgroundColor: theme.palette.action.disabled,
                          color: theme.palette.action.disabledBackground
                        }
                      }}
                    >
                      {invitingPlayer === player.puuid ? 'Inviting...' : 'Invite'}
                    </Button>
                  </ListItem>
                ))
              )}
            </List>
          </DialogContent>
        </Dialog>

        {/* Match Found Dialog - ESEA Style */}
        <Dialog 
          open={matchFound} 
          maxWidth="sm"
          PaperProps={{
            sx: { 
              backgroundColor: '#1a1a1a',
              border: '2px solid #333',
              borderRadius: '8px',
              minWidth: '400px',
              maxWidth: '450px',
              boxShadow: '0 8px 32px rgba(0,0,0,0.8)'
            }
          }}
        >
          <DialogContent sx={{ p: 2, textAlign: 'center', position: 'relative' }}>
            {/* Close button */}
            <IconButton
              onClick={handleDeclineMatch}
              sx={{
                position: 'absolute',
                top: 8,
                right: 8,
                color: '#888',
                '&:hover': {
                  color: '#fff',
                  backgroundColor: 'rgba(255,255,255,0.1)'
                }
              }}
            >
              ✕
            </IconButton>
            {/* Header */}
            <Box sx={{ mb: 2 }}>
              <Typography 
                variant="h5" 
                sx={{ 
                  color: '#fff',
                  fontWeight: 'bold',
                  fontFamily: '"Source Sans Pro", sans-serif',
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                  mb: 0.5,
                  fontSize: '20px'
                }}
              >
                Match Ready
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ 
                  color: '#ccc',
                  fontFamily: '"Source Sans Pro", sans-serif',
                  fontSize: '13px'
                }}
              >
                Confirm your match
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ 
                  color: '#ccc',
                  fontFamily: '"Source Sans Pro", sans-serif',
                  mb: 0.5,
                  fontSize: '13px'
                }}
              >
                for the <span style={{ color: theme.palette.secondary.main, fontWeight: 'bold' }}>COMPETITIVE 5v5</span>
              </Typography>
            </Box>

            {/* Show different content based on user acceptance state */}
            {!userAccepted ? (
              <>
                {/* Countdown Timer with Gauge - Only show if user hasn't accepted */}
                <Box sx={{ mb: 1.5 }}>
                  <Box
                    sx={{
                      width: '52px',
                      height: '52px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto',
                      position: 'relative',
                      background: 'linear-gradient(135deg, rgba(212, 160, 255, 0.1) 0%, rgba(212, 160, 255, 0.05) 100%)'
                    }}
                  >
                    {/* Gauge Background Circle */}
                    <svg
                      width="52"
                      height="52"
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        transform: 'rotate(-90deg)'
                      }}
                    >
                      {/* Background circle */}
                      <circle
                        cx="26"
                        cy="26"
                        r="19"
                        fill="none"
                        stroke="rgba(212, 160, 255, 0.2)"
                        strokeWidth="3"
                      />
                      {/* Progress circle */}
                      <circle
                        cx="26"
                        cy="26"
                        r="19"
                        fill="none"
                        stroke={theme.palette.secondary.main}
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeDasharray={`${2 * Math.PI * 19}`}
                        strokeDashoffset={`${2 * Math.PI * 19 * (1 - (timeLeft / 30))}`}
                        style={{
                          transition: 'stroke-dashoffset 0.5s ease-in-out'
                        }}
                      />
                    </svg>
                    <Typography 
                      variant="body1" 
                      sx={{ 
                        color: theme.palette.secondary.main,
                        fontWeight: 'bold',
                        fontFamily: '"Source Sans Pro", sans-serif',
                        fontSize: '19px',
                        zIndex: 1
                      }}
                    >
                      {timeLeft}
                    </Typography>
                  </Box>
                </Box>

                {/* Action Button - Only show if user hasn't accepted */}
                <Button
                  variant="contained"
                  onClick={handleAcceptMatch}
                  autoFocus
                  sx={{
                    backgroundColor: theme.palette.secondary.main,
                    color: '#000',
                    fontWeight: 'bold',
                    textTransform: 'uppercase',
                    letterSpacing: '1px',
                    fontFamily: '"Source Sans Pro", sans-serif',
                    fontSize: '12px',
                    px: 3,
                    py: 1,
                    borderRadius: '4px',
                    border: 'none',
                    boxShadow: '0 3px 8px rgba(212, 160, 255, 0.3)',
                    '&:hover': {
                      backgroundColor: '#c490ff',
                      boxShadow: '0 4px 12px rgba(212, 160, 255, 0.4)',
                    },
                    '&:active': {
                      transform: 'translateY(1px)',
                    }
                  }}
                >
                  Accept
                </Button>
              </>
            ) : (
              <>
                {/* Show acceptance progress when user has accepted */}
                <AcceptanceProgress />
                
                {/* Time remaining */}
                <Typography 
                  variant="body2" 
                  sx={{ 
                    color: theme.palette.secondary.main,
                    fontFamily: '"Source Sans Pro", sans-serif',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    mt: 1
                  }}
                >
                  {timeLeft}s remaining
                </Typography>
              </>
            )}
          </DialogContent>
        </Dialog>
      </Box>
    </Container>
  );
};

export default PugQueue;
