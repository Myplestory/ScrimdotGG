# Client Frontend (React/Electron) - Function Reference

Sorted by file and grouped by functionality/logic flow. See `frontend/index.rst` for overview.

## WebSocket Context and Navigation

### src/contexts/WebSocketContext.jsx
- WebSocketProvider({ children }): Provides WS connection, state, and API
- useWebSocket(): Hook exposing connection status, data, sendEvent, on/off

### src/components/GlobalMatchButton.jsx
- GlobalMatchButton(): Floating navigation to active match

### src/App.jsx
- App(): Routes and layout
- MatchPageWrapper(): Binds URL param to `MatchPage`
- Logout({ setAuthenticated }): Clears session and returns to login

## Match Page Flow (Phases and UI)

### src/pages/MatchPage.jsx
- MatchPage(): Orchestrates phase rendering and event subscriptions
- getMatchPhase(matchData): Derives current phase
- handleVetoMapAction(mapName): Sends veto map
- handleSideSelection(side): Sends side selection
- handleJoinGame(payload): Handles join_custom_game event

### src/pages/components (examples)
- VetoPhase({ matchData }): Interactive map veto
- SideSelectionPhase({ matchData }): Side selection UI
- WaitingForGamePhase({ matchData }): Constructor creating game
- LiveMatchPhase({ matchData }): Live score/stats

## Queue and Lobby

### src/pages/PugQueue.jsx
- PugQueue(): Queue UI and actions
- handleFindMatch(): Initiates matchmaking
- handleJoinQueue()/handleLeaveQueue(): Queue membership
- sendLobbyMessage(message, lobbyId): Lobby chat

### src/components/lobby/lobby.jsx
- Lobby(): Lobby screen and interactions
- handlePlayClick(): Queue lobby
- handleAccept()/handleDecline(): Match acceptance

### src/components/lobby/playerslot.jsx
- PlayerSlot({ player, handleEmptySlotClick, slotIndex }): Renders slot

## Authentication and Layout

### src/pages/login.jsx
- AuthenticationScreen({ onAuthentication }): Login flow

### src/pages/layout.jsx
- Layout({ children, setActiveComponent }): App shell and drawer

## Utilities and Theming

### src/utils/maps.js
- mapSlug(name): Stable slug for a map name
- mapImageUrl(name, overrideUrl?): Returns image URL

### src/utils/rankprog.jsx
- getRankAndProgress(elo): Returns display rank and progress

### src/components/SimpleRankGauge.jsx
- SimpleRankGauge({ elo, size }): Gauge UI for rank

### src/components/StatusIndicator.jsx
- StatusIndicator(props): Connection/auth status indicator

### src/theme.js
- tokens(mode): Design tokens
- themeSettings(mode): MUI theme config
- useMode(): Dark/light mode hook

## Misc Components

### src/components/*
- Title, LoadingScreen, Chart, SelectBar, RankWidget, Home components: Presentational helpers used across pages

Notes:
- Event names and payload shapes are defined in `docs/Server/*` and `docs/Client/backend/*`.
- Match page subcomponents should follow phase naming and reside under a dedicated folder if expanded further.
