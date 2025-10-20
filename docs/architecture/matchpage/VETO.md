# Match Page & Veto System Implementation

## Overview
This document details the system flow for the match page veto functionality.

---

## Components (References)

- Server models and veto handlers: see `docs/Server/matchpage.md`.
- Client UI and event handling: see `docs/Client/frontend/matchpage.md`.

---

## Data Flow

1. All players accept → server emits `match_confirmed` → clients redirect to `/match/{matchId}`
2. Server starts veto (`veto_started`) with current team, deadline, available maps
3. Captains perform actions (`veto_map`) → server validates and emits `map_vetoed`
4. On last remaining map → server emits `veto_complete` with `final_map` and `side_selector`

---

## Event Payloads (Server → Client)

- `veto_started`: `match_id`, `current_turn`, `available_maps`, `deadline`
- `map_vetoed`: `match_id`, `map`, `vetoed_by`, `next_turn`, `remaining_maps`, `deadline`
- `veto_complete`: `match_id`, `final_map`, `side_selector`

See `docs/Server/matchpage.md` for full payload shapes.

---

## Timing

- Veto turn deadline: 30 seconds (auto-veto on timeout)
- Side selection deadline: 15 seconds

---

 


