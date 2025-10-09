# Directory Restructure Plan

## Current Structure (Messy):
```
Scrimdotgg/
├── Scrim.GG_Client/
│   └── scrimgg/
│       ├── backend/
│       └── frontend/
│           └── scrimgg/
└── ScrimGG/
    └── scrimgg/
        ├── server/
        │   └── scrimgg/
        └── react-frontend/
            └── scrimgg/
```

## New Structure (Clean):
```
scrimgg/
├── client/                 # Desktop client (Electron app)
│   ├── backend/           # Python local backend
│   │   ├── bootstrap.py
│   │   ├── clientapi.py
│   │   ├── pugapi.py
│   │   ├── Pipfile
│   │   └── ...
│   └── frontend/          # React + Electron UI
│       ├── src/
│       ├── public/
│       ├── main.js
│       ├── package.json
│       └── ...
├── server/                # Django matchmaking server
│   ├── manage.py
│   ├── Pipfile
│   ├── scrimgg/          # Main Django app
│   ├── matchmaking/      # Matchmaking app
│   ├── lobby/
│   ├── riotlogin/
│   └── ...
├── docs/                  # Documentation
│   ├── ARCHITECTURE_IMPROVEMENTS.md
│   ├── IMPLEMENTATION_ROADMAP.md
│   ├── WEBSOCKET_REFACTOR_SUMMARY.md
│   └── QUICK_START.md
├── examples/              # Reference implementations
│   ├── 1_websocket_client_hook.jsx
│   ├── 2_improved_quart_backend.py
│   └── ...
├── .gitignore
├── README.md
├── LICENSE
└── GITHUB_SETUP.md
```

## Benefits:
- ✅ Clear separation: `client/` vs `server/`
- ✅ No unnecessary nesting
- ✅ Easier navigation
- ✅ Professional structure
- ✅ Matches industry standards

