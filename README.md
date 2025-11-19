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

## UI Showcase

<style>
.play-gallery input, .league-gallery input, .tournament-gallery input { display: none; }
.play-gallery img, .league-gallery img, .tournament-gallery img { display: none; max-width: 100%; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.6); }
#play1:checked ~ div img:nth-child(1), #play2:checked ~ div img:nth-child(2), #play3:checked ~ div img:nth-child(3) { display: block; margin: 0 auto; }
#league1:checked ~ div img:nth-child(1), #league2:checked ~ div img:nth-child(2), #league3:checked ~ div img:nth-child(3), #league4:checked ~ div img:nth-child(4), #league5:checked ~ div img:nth-child(5) { display: block; margin: 0 auto; }
#tournament1:checked ~ div img:nth-child(1), #tournament2:checked ~ div img:nth-child(2), #tournament3:checked ~ div img:nth-child(3), #tournament4:checked ~ div img:nth-child(4) { display: block; margin: 0 auto; }
.play-gallery, .league-gallery, .tournament-gallery { text-align: center; margin: 20px 0; }
.play-gallery label, .league-gallery label, .tournament-gallery label { 
  background: rgba(255,70,85,0.2); 
  border: 2px solid #FF4655; 
  color: #FF4655; 
  padding: 8px 16px; 
  margin: 0 5px; 
  border-radius: 4px; 
  cursor: pointer; 
  display: inline-block;
  font-weight: bold;
}
.play-gallery label:hover, .league-gallery label:hover, .tournament-gallery label:hover { 
  background: rgba(255,70,85,0.3); 
}
</style>

### Play community pickup games with ScrimGG

<div class="play-gallery">
  <input type="radio" name="play" id="play1" checked>
  <input type="radio" name="play" id="play2">
  <input type="radio" name="play" id="play3">
  <div>
    <img src="./docs/images/Play/pug1.png" alt="PUG Matchmaking">
    <img src="./docs/images/Play/pug2.png" alt="PUG Lobby">
    <img src="./docs/images/Play/pug3.png" alt="PUG Game">
  </div>
  <div style="margin-top: 15px;">
    <label for="play1">1</label>
    <label for="play2">2</label>
    <label for="play3">3</label>
  </div>
</div>

### Etch your mark in the community with the official ScrimGG League system, featuring cash prizes and more

<div class="league-gallery">
  <input type="radio" name="league" id="league1" checked>
  <input type="radio" name="league" id="league2">
  <input type="radio" name="league" id="league3">
  <input type="radio" name="league" id="league4">
  <input type="radio" name="league" id="league5">
  <div>
    <img src="./docs/images/League/League1.png" alt="League Overview">
    <img src="./docs/images/League/League2.png" alt="League Standings">
    <img src="./docs/images/League/League3.png" alt="League Details">
    <img src="./docs/images/League/League4.png" alt="League Rankings">
    <img src="./docs/images/League/League5.png" alt="League Stats">
  </div>
  <div style="margin-top: 15px;">
    <label for="league1">1</label>
    <label for="league2">2</label>
    <label for="league3">3</label>
    <label for="league4">4</label>
    <label for="league5">5</label>
  </div>
</div>

### Host your own tournaments, sponsor them, and grow your own community

<div class="tournament-gallery">
  <input type="radio" name="tournament" id="tournament1" checked>
  <input type="radio" name="tournament" id="tournament2">
  <input type="radio" name="tournament" id="tournament3">
  <input type="radio" name="tournament" id="tournament4">
  <div>
    <img src="./docs/images/Tournaments/tournament1.png" alt="Tournament View">
    <img src="./docs/images/Tournaments/tournament2.png" alt="Tournament Bracket">
    <img src="./docs/images/Tournaments/tournament3.png" alt="Tournament Details">
    <img src="./docs/images/Tournaments/tournament4.png" alt="Tournament Results">
  </div>
  <div style="margin-top: 15px;">
    <label for="tournament1">1</label>
    <label for="tournament2">2</label>
    <label for="tournament3">3</label>
    <label for="tournament4">4</label>
  </div>
</div>

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
| **[Architecture](./docs/architecture/)** | System design, matchmaking, and architecture docs |
| **[Client](./docs/Client/)** | Frontend and backend client documentation |
| **[Server](./docs/Server/)** | Server-side app documentation |
| **[Implementation](./docs/implementation/)** | Implementation guides and technical docs |
| **[Testing & Bots](./docs/testing/)** | Bot framework, testing commands |
| **[Troubleshooting](./docs/troubleshooting/)** | Common issues and quick fixes |
| **[Setup Guide](./docs/setup/)** | Installation and configuration |

## Features

### Client Features
- WebSocket-based real-time communication
- Valorant client integration
- Lobby creation and party management
- Real-time chat system
- Player authentication
- Game state monitoring
- Automatic match detection
- Map/server veto system
- Player verification (all 10 joined custom game)
- Automated match result collection
- Post-match ELO/MMR updates
- Comprehensive stats tracking
- Friend system
- Team management
- Tournament system
- Anti-cheat integration
- Admin moderation panel

### Server Features
- Queue system with Redis backend
- MMR/ELO hybrid rating system
- TrueSkill integration for skill estimation
- Time-based matchmaking tolerance
- Match acceptance flow (30s timeout)
- Automatic requeueing on timeout
- Rank-aware matchmaking (5 MMR tiers)

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

