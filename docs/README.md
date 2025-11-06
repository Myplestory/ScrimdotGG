# 📚 Scrim.GG Documentation

Welcome to the Scrim.GG documentation hub. This directory contains comprehensive guides for understanding the codebase architecture, implementation details, and development workflows.

---

## 📁 Documentation Structure

The documentation is organized into four main categories:

### 🏗️ **[Architecture/](architecture/)**
System design, flows, and architectural decisions
- **[matchmaking/](architecture/matchmaking/)** - Matchmaking algorithm, MMR/ELO systems, tolerance, and requeueing
- **[system/](architecture/system/)** - System architecture and improvements
- **[legacy/](architecture/legacy/)** - Historical architecture documents

### 💻 **[Client/](Client/)**
Client-side documentation (React/Electron frontend + Quart backend)
- **[frontend/](Client/frontend/)** - React/Electron application documentation
- **[backend/](Client/backend/)** - Quart ASGI layer and valclient middleware

### 🖥️ **[Server/](Server/)**
Server-side application documentation
- Per-app function documentation (users, lobby, match_system, matchmaking, riotlogin, etc.)

### 🔧 **[Implementation/](implementation/)**
Implementation guides, setup, testing, and deployment
- **[Setup/](implementation/Setup/)** - Development setup and deployment guides
- **[Testing/](implementation/Testing/)** - Testing frameworks and procedures
- **[Troubleshooting/](implementation/Troubleshooting/)** - Common issues and solutions
- **[Features/](implementation/Features/)** - Feature implementation guides
- **[Server-Refactor/](implementation/Server-Refactor/)** - Backend refactoring documentation

---

## 🎯 Quick Start Guide

### For New Developers
1. **Start Here**: [Development Setup](implementation/Setup/DEVELOPMENT_SETUP.md)
2. **Architecture Overview**: [Matchmaking System](architecture/matchmaking/README.md)
3. **Function Reference**: [Server Apps](Server/) and [Client Components](Client/)

### For Understanding Matchmaking
1. **[Matchmaking Overview](architecture/matchmaking/README.md)** - System overview
2. **[MMR/ELO System](architecture/matchmaking/MMR_ELO_SYSTEM.md)** - Rating system details
3. **[TrueSkill](architecture/matchmaking/TRUESKILL.md)** - TrueSkill integration
4. **[Priority Bias](architecture/matchmaking/PRIORITY_BIAS.md)** - Fairness mechanisms
5. **[Requeue Logic](architecture/matchmaking/REQUEUE.md)** - Timeout handling

### For Development
1. **[Testing Guide](implementation/Testing/TESTING_GUIDE.md)** - How to test
2. **[Production Deployment](implementation/Setup/PRODUCTION_DEPLOYMENT.md)** - Deployment guide
3. **[Troubleshooting](implementation/Troubleshooting/)** - Common issues

---

## 🔗 Key Documents

### Architecture
- [Matchmaking System](architecture/matchmaking/README.md) - Core matchmaking overview
- [MMR/ELO System](architecture/matchmaking/MMR_ELO_SYSTEM.md) - Rating system design
- [TrueSkill Integration](architecture/matchmaking/TRUESKILL.md) - Probabilistic ratings
- [Priority Bias](architecture/matchmaking/PRIORITY_BIAS.md) - Fairness mechanisms

### Implementation
- [Development Setup](implementation/Setup/DEVELOPMENT_SETUP.md) - Getting started
- [Testing Guide](implementation/Testing/TESTING_GUIDE.md) - Testing procedures
- [Production Deployment](implementation/Setup/PRODUCTION_DEPLOYMENT.md) - Deployment guide

### Function Documentation
- [Server Functions](Server/) - All server app functions
- [Client Functions](Client/) - Frontend and backend client functions

---

## 📊 System Overview

### Core Components
- **Matchmaking**: MMR-based matching with TrueSkill uncertainty
- **Rating System**: Hybrid MMR (hidden) + ELO (display) with adaptive weighting
- **Requeue Logic**: Smart requeueing with priority bias for compliant players
- **Client Architecture**: React/Electron frontend + Quart ASGI backend
- **Server Architecture**: Django-based with Celery task queue

### Key Features
- ✅ **Skill-based Matchmaking**: TrueSkill with uncertainty tracking
- ✅ **Fair Requeueing**: Priority bias for accepting players
- ✅ **Adaptive Tolerance**: Time-based matchmaking range expansion
- ✅ **Real-time Updates**: WebSocket communication
- ✅ **Bot Testing**: Comprehensive testing framework

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- Redis
- PostgreSQL (optional, SQLite for development)

### Quick Setup
```bash
# 1. Clone and setup
git clone <repository>
cd Scrimdotgg

# 2. Server setup
cd server
pipenv install
pipenv run python manage.py migrate

# 3. Client setup
cd ../client
pipenv install  # Backend
cd frontend
npm install     # Frontend

# 4. Start services
# Server: pipenv run python manage.py runserver
# Client backend: pipenv run python run.py
# Client frontend: npm start
```

### Next Steps
1. Read [Development Setup](implementation/Setup/DEVELOPMENT_SETUP.md) for detailed instructions
2. Explore [Matchmaking System](architecture/matchmaking/README.md) to understand the core algorithm
3. Check [Testing Guide](implementation/Testing/TESTING_GUIDE.md) to run tests

---

## 📞 Support

- **Architecture Questions**: Check [Architecture/](architecture/) documentation
- **Implementation Issues**: See [Implementation/](implementation/) guides
- **Function Reference**: Browse [Server/](Server/) and [Client/](Client/) docs
- **Common Problems**: [Troubleshooting](implementation/Troubleshooting/) section

---

## 🎉 Contributing

1. **Read the docs** - Start with the relevant architecture or implementation guide
2. **Follow patterns** - Check existing function documentation for style
3. **Test thoroughly** - Use the testing framework and bot system
4. **Update docs** - Keep documentation current with code changes

---

*Last updated: October 2025*  
*Documentation organized by: Architecture Team*