# Match Page (Client - Frontend)

Comprehensive frontend documentation for the Match Page: routing, components, context, and event handling.

## Routing
```javascript
// client/frontend/src/App.jsx
<Routes>
  <Route path="/match/:matchId" element={<MatchPage />} />
</Routes>
```

## Global Navigation
```javascript
// client/frontend/src/contexts/MatchContext.jsx
export const MatchContext = createContext();
export function MatchProvider({ children }) {
  const [activeMatch, setActiveMatch] = useState(null);
  const [matchState, setMatchState] = useState(null);
  useEffect(() => {
    if (!ws) return;
    const handleMatchConfirmed = (data) => {
      setActiveMatch(data.match_id);
      setMatchState('CONFIRMED');
      navigate(`/match/${data.match_id}`);
    };
    ws.on('match_confirmed', handleMatchConfirmed);
    return () => ws.off('match_confirmed', handleMatchConfirmed);
  }, [ws]);
  return (
    <MatchContext.Provider value={{ activeMatch, matchState, setActiveMatch, setMatchState }}>
      {children}
    </MatchContext.Provider>
  );
}
```

## Global "Match in Progress" Button
```javascript
// client/frontend/src/components/GlobalMatchButton.jsx
export function GlobalMatchButton() {
  const { activeMatch, matchState } = useContext(MatchContext);
  const navigate = useNavigate();
  const location = useLocation();
  if (!activeMatch || location.pathname.includes('/match/')) return null;
  return (
    <FloatingButton onClick={() => navigate(`/match/${activeMatch}`)} className="pulse-animation">
      <GameIcon />
      <span>Match in Progress</span>
      <Badge>{getMatchPhaseLabel(matchState)}</Badge>
    </FloatingButton>
  );
}
```

## Match Page Component
```javascript
// client/frontend/src/pages/MatchPage.jsx
export function MatchPage() {
  const { matchId } = useParams();
  const { ws } = useContext(WebSocketContext);
  const [matchData, setMatchData] = useState(null);
  const [phase, setPhase] = useState('loading');
  useEffect(() => { ws.send('get_match_data', { match_id: matchId }); }, [matchId]);
  useEffect(() => {
    ws.on('match_data', setMatchData);
    ws.on('veto_started', handleVetoStarted);
    ws.on('map_vetoed', handleMapVetoed);
    ws.on('veto_complete', handleVetoComplete);
    ws.on('side_selected', handleSideSelected);
    ws.on('join_custom_game', handleJoinGame);
    ws.on('match_starting', handleMatchStarting);
    return () => { ws.off('match_data', setMatchData); /* ... */ };
  }, [ws]);
  return (
    <div className="match-page">
      {phase === 'VETO' && <VetoPhase matchData={matchData} />}
      {phase === 'SIDE_SELECTION' && <SideSelectionPhase matchData={matchData} />}
      {phase === 'CREATING' && <WaitingForGamePhase matchData={matchData} />}
      {phase === 'IN_PROGRESS' && <LiveMatchPhase matchData={matchData} />}
    </div>
  );
}
```

## Client → Server Events
```javascript
// Veto
sendEvent('veto_map', { match_id, map });
// Side Selection
sendEvent('select_side', { match_id, side });
// Pregame joined
sendEvent('player_joined_pregame', { match_id, success: true });
```
