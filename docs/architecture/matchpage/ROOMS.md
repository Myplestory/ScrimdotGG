# Match Room Page Specification

## Overview
The Match Room is a dedicated page for each match where participants can interact, veto maps, view teams, and spectators can watch live stats.

---

## URL Structure

```
/match/:matchId
```

**Example**: `/match/a3f4b2e1-5678-1234-abcd-ef9876543210`

---

## Access Control

### **Participants** (10 players in the match)
- Full access to match room
- Can participate in map veto
- Can see team voice chat info
- Can ready up
- Can see match configuration

### **Spectators** (non-participants)
- Read-only access
- Can view teams, stats, scores
- Cannot participate in veto
- Cannot see voice chat details
- Cannot interact with match controls

### **Public/Private**
- All matches are **publicly viewable** by default
- Future: Add private match option

---

## Page Layout

### **Header Section**
```
┌─────────────────────────────────────────────────────────┐
│  MATCH #A3F4B2E1                    [LIVE] 🔴          │
│  5v5 Competitive • Virginia Server • Started 2m ago    │
└─────────────────────────────────────────────────────────┘
```

**Data**:
- Match ID (short version, first 8 chars)
- Match status (WAITING / VETO / LIVE / COMPLETED)
- Game mode (5v5 Competitive)
- Server region
- Time elapsed/remaining

---

### **Team Display**

```
┌──────────────── TEAM A ────────────────┐  ┌──────────────── TEAM B ────────────────┐
│ ⭐ Captain: evisc#erate                │  │ ⭐ Captain: Player5                     │
│                                        │  │                                        │
│ Players:                               │  │ Players:                               │
│  1. evisc#erate    [READY] ✅  A 6493 │  │  1. Player5        [READY] ✅  A 6400  │
│  2. Player2        [READY] ✅  A 6450 │  │  2. Player6        [WAIT]  ⏳  A 6350  │
│  3. Player3        [WAIT]  ⏳  A- 6100 │  │  3. Player7        [READY] ✅  B+ 5900 │
│  4. Player4        [READY] ✅  B+ 5950 │  │  4. Player8        [READY] ✅  B  5700 │
│  5. QueueBot1      [READY] ✅  A 6500 │  │  5. QueueBot5      [READY] ✅  A 6480  │
│                                        │  │                                        │
│ Avg MMR: 6180      Avg ELO: 6299      │  │ Avg MMR: 6165      Avg ELO: 6266      │
│ Discord: [JOIN VOICE] 🎙️              │  │ Discord: [JOIN VOICE] 🎙️              │
└────────────────────────────────────────┘  └────────────────────────────────────────┘
```

**Data per player**:
- Alias
- Ready status (READY ✅ / WAITING ⏳)
- Display rank + ELO
- Captain indicator (⭐)

**Team stats**:
- Average MMR (hidden from spectators, shown to participants)
- Average Display ELO
- Discord voice channel link (participants only)

---

### **Map Veto Phase**

```
┌──────────────────────────────────────────────────────────────────────┐
│                          MAP VETO                                    │
│  Team A Captain's Turn • Action: BAN                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  [Ascent]     [Bind]      [Breeze]    [Fracture]   [Haven]          │
│   Available   Available    Available   Available   Available         │
│                                                                       │
│  [Icebox]     [Lotus]     [Pearl]     [Split]                       │
│   BANNED (A)  Available   Available   Available                      │
│                                                                       │
│  Veto History:                                                       │
│  1. Team A banned Icebox                                            │
│  2. Waiting for Team A...                                           │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

**Veto Process** (Standard competitive format):
1. Team A **bans** 1 map
2. Team B **bans** 1 map
3. Team A **picks** 1 map (Map 1)
4. Team B **picks** 1 map (Map 2)
5. Team A **bans** 1 map
6. Team B **bans** 1 map
7. Remaining map = **Decider** (Map 3, if needed)

**Final result**: Best of 3 (BO3) with predetermined map order

**UI Elements**:
- Map cards showing map name + thumbnail
- Visual indication of status (Available / Banned / Picked)
- Turn indicator (which captain's turn)
- Action indicator (BAN / PICK)
- Veto history log
- Countdown timer per veto turn (30 seconds, auto-random if timeout)

---

### **Match Configuration**

```
┌──────────────────────────────────────────────────────────────────────┐
│                      MATCH SETTINGS                                  │
├──────────────────────────────────────────────────────────────────────┤
│  Format: Best of 3 (BO3)                                            │
│  Overtime: MR3 (First to 13 wins)                                   │
│  Server: Virginia (NA East)                                         │
│  Game Server: Connecting...                                         │
│                                                                       │
│  Maps:                                                               │
│  1. Ascent (Team A pick)                                            │
│  2. Haven (Team B pick)                                             │
│  3. Bind (Decider, if needed)                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

### **Live Match Stats** (During game)

```
┌──────────────────────────────────────────────────────────────────────┐
│                    LIVE MATCH - Map 1: Ascent                        │
│                    TEAM A [5] - [4] TEAM B                           │
│                    Round 10/24 • ATK/DEF                             │
├──────────────────────────────────────────────────────────────────────┤
│  Team A (ATK)                                           Team B (DEF) │
│  ┌─────────────────────────────────────────┐  ┌─────────────────────┤
│  │ Player        K  D  A  ACS  ADR         │  │ Player      K  D  A │
│  │ evisc#erate   12 8  3  245  150         │  │ Player5    10 10 5  │
│  │ Player2       10 9  5  220  145         │  │ Player6     9 11 4  │
│  │ Player3        8 10 7  200  130         │  │ Player7    11  9 6  │
│  │ Player4        9  9  4  215  140         │  │ Player8     8 10 3  │
│  │ QueueBot1     11  8  6  230  148         │  │ QueueBot5  10  8 7  │
│  └─────────────────────────────────────────┘  └─────────────────────┘
└──────────────────────────────────────────────────────────────────────┘
```

**Live data** (updates every 5-10 seconds):
- Current score
- Round number
- Round timer
- Player stats (K/D/A, ACS, ADR)
- Economy (if available from game server)

---

## Backend Data Structure

- See `docs/Server/matchpage.md` for server-side model definitions.

---

## WebSocket Events

- Participant events and payloads: see `docs/Server/matchpage.md` (server → client) and `docs/Client/frontend/matchpage.md` (client handlers).

---

 

