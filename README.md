# Scrim.GG - Competitive Valorant Matchmaking Platform

<div align="center">

![Scrim.GG](https://img.shields.io/badge/Scrim.GG-Valorant-ff4655?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A third-party competitive matchmaking and scrim service for Valorant, tailored specifically for serious players who want to elevate their gameplay to the next level.**

</div>

---

## Overview

Scrim.GG is a comprehensive matchmaking platform that provides highly engaged players with:
- ELO/MMR-based competitive matchmaking with TrueSkill integration
- Organized 5v5 PUG matches
- Scrim finder and organizer
- Detailed player statistics and rankings
- Real-time lobby chat and communication
- Clans and team support
- Tournament capabilities
- Monthly elo ladders with cash rewards
- Admin support for dispute resolution, player assistance, and fair play
- Karma and social/matchmaking block system for community self governance
- Forums for team recruitment, community growth, and networking for players of all skill levels


## Architecture

### 1. Django ASGI Server (`server/`)
- MMR-based matchmaking with time tolerance and priority requeue bias
- Django Channels for WebSocket consumer support
- Redis for caching, queues, state management, and async to sync support
- PostgreSQL database
- Celery for concurrent batched synchronous tasks

### 2. User Client (`client/`)
- ElectronJs Desktop application
- React frontend with Material-UI
- Lightweight ASGI Python backend (Quart)
- WebSocket communication with server
- Valorant local client API

## Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 16+**
- **Redis Server**
- **PostgreSQL**
- **Valorant** (for client testing)

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/scrimgg.git
cd scrimgg
```

#### 2. Server Setup
```bash
cd server
pipenv install
pipenv shell
python manage.py migrate
python manage.py runserver
```

#### 3. Redis (Required)
```bash
# Windows (using WSL or Redis Windows port)
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis
```

#### 4. Client Backend
```bash
cd client/backend
pipenv install
pipenv shell
python bootstrap.py
```

#### 5. Client Frontend
```bash
cd client/frontend
npm install
npm start
```

## Documentation

**[📚 Complete Documentation →](./docs/README.md)**

### Quick Links

| Category | Description |
|----------|-------------|
| **[Matchmaking System](./docs/matchmaking/)** | MMR/ELO system, algorithms, requeueing |
| **[Testing & Bots](./docs/testing/)** | Bot framework, testing commands |
| **[Troubleshooting](./docs/troubleshooting/)** | Common issues and quick fixes |
| **[Setup Guide](./docs/setup/)** | Installation and configuration |
| **[Quick Start](./docs/QUICK_START.md)** | Get up and running quickly |
| **[Architecture](./docs/ARCHITECTURE_IMPROVEMENTS.md)** | System design overview |

## Features

### ✅ Implemented
- WebSocket-based real-time communication
- Valorant client integration
- Lobby creation and party management
- Real-time chat system
- Queue system with Redis backend
- Player authentication
- **MMR/ELO hybrid rating system**
- **TrueSkill integration for skill estimation**
- **Time-based matchmaking tolerance**
- **Match acceptance flow (30s timeout)**
- **Automatic requeueing on timeout**
- **Rank-aware matchmaking (5 MMR tiers)**

### In Development
- Game state monitoring
- Automatic match detection
- Map/server veto system
- Player verification (all 10 joined custom game)

### Planned
- Automated match result collection
- Post-match ELO/MMR updates
- Comprehensive stats tracking
- Friend system
- Team management
- Tournament system
- Anti-cheat integration
- Admin moderation panel

## Tech Stack

### Backend
- **Django 5.0** - Web framework
- **Django Channels** - WebSocket support (via Daphne ASGI server)
- **Redis** - Caching, queues, and channel layer
- **Celery + Beat** - Background tasks and scheduling
- **PostgreSQL** - Primary database
- **TrueSkill** - Skill rating algorithm

### Client
- **Electron** - Desktop app framework
- **React 18** - UI framework
- **Material-UI** - Component library
- **Quart** - Async Python web framework (local backend)
- **valclient** - Valorant local API wrapper

### Infrastructure
- **Daphne** - ASGI server for WebSockets
- **Redis Server** - In-memory data store
- **Docker** (optional) - Containerization
- **Nginx** (production) - Reverse proxy

## Performance

Optimized for running alongside Valorant:

- **Memory Usage:** ~30-50MB (client), ~150-200MB (server)
- **CPU Usage:** <1% idle, ~3% active
- **WebSocket Latency:** ~10-15ms average
- **Matchmaking Speed:** ~10-50ms per run
- **FPS Impact:** <1 frame drop

## Contributing

Contributions are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [DEVELOPMENT_SETUP.md](./docs/DEVELOPMENT_SETUP.md) for development environment setup.

## Development Status

| Component | Status | Progress |
|-----------|--------|----------|
| WebSocket Communication | ✅ Complete | 100% |
| Lobby System | ✅ Complete | 100% |
| Chat System | ✅ Complete | 100% |
| Queue System | ✅ Complete | 100% |
| **Matchmaking (MMR/ELO)** | ✅ Complete | 100% |
| **Match Acceptance Flow** | ✅ Complete | 100% |
| **Requeueing System** | ✅ Complete | 100% |
| Game Monitor | 🚧 In Progress | 40% |
| Match Coordinator | 🚧 In Progress | 30% |
| Veto System | 📋 Planned | 0% |
| Post-Match Stats/Updates | 📋 Planned | 0% |

**Current Focus:** Game state monitoring and custom game coordination

## Disclaimer

This is a third-party application and is not affiliated with, endorsed by, or connected to Riot Games. Use at your own risk. This project is for educational purposes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by [FACEIT](https://www.faceit.com)
- Built with [valclient](https://github.com/colinhartigan/valclient-python)
- UI design inspired by ESEA
- TrueSkill algorithm by Microsoft Research

---

<div align="center">

**Made for the Valorant competitive community**

</div>

