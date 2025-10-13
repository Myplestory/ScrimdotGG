# Scrim.GG Documentation

Comprehensive documentation for the Scrim.GG matchmaking platform.

---

## Documentation Structure

### [Matchmaking](./matchmaking/)
Core matchmaking system documentation including algorithms, requeueing, and MMR/ELO systems.

**Key Documents:**
- **[MMR_ELO_SYSTEM.md](./matchmaking/MMR_ELO_SYSTEM.md)** - Hybrid MMR/ELO rating system
- **[TRUESKILL_INTEGRATION.md](./matchmaking/TRUESKILL_INTEGRATION.md)** - TrueSkill integration for skill estimation
- **[MATCHMAKING_SCHEDULE_ANALYSIS.md](./matchmaking/MATCHMAKING_SCHEDULE_ANALYSIS.md)** - Optimal scheduling for matchmaker and cleanup tasks
- **[PRIORITY_BIAS_STATUS.md](./matchmaking/PRIORITY_BIAS_STATUS.md)** - Adaptive weighting and time tolerance

**Requeue System:**
- [ALL_REQUEUE_FIXES_FINAL_SUMMARY.md](./matchmaking/ALL_REQUEUE_FIXES_FINAL_SUMMARY.md) - Complete requeue fix summary
- [FINAL_REQUEUE_FIXES_COMPLETE.md](./matchmaking/FINAL_REQUEUE_FIXES_COMPLETE.md) - Final implementation details
- [COMPREHENSIVE_REQUEUE_ANALYSIS.md](./matchmaking/COMPREHENSIVE_REQUEUE_ANALYSIS.md) - In-depth analysis
- [CRITICAL_BUG_FOUND_MATCH_LOBBIES.md](./matchmaking/CRITICAL_BUG_FOUND_MATCH_LOBBIES.md) - Critical bug fix for lobby data preservation

---

### [Testing](./testing/)
Testing infrastructure, bot systems, and test scripts documentation.

**Key Documents:**
- **[README.md](./testing/README.md)** - Testing overview and quick start
- **[BOT_TEST_V2_UPDATED.md](./testing/BOT_TEST_V2_UPDATED.md)** - Bot testing framework v2
- **[BOT_WEBSOCKET_IMPLEMENTATION_COMPLETE.md](./testing/BOT_WEBSOCKET_IMPLEMENTATION_COMPLETE.md)** - WebSocket-based bot testing
- **[TESTING_COMMANDS.md](./testing/TESTING_COMMANDS.md)** - Quick reference for test commands
- [PHASE2_REMATCH_TEST_ADDED.md](./testing/PHASE2_REMATCH_TEST_ADDED.md) - Rematch testing functionality

---

### [Client UI](./client-ui/)
Frontend user interface documentation and fixes.

**Key Documents:**
- **[MODAL_AND_TIMING_FIXES.md](./client-ui/MODAL_AND_TIMING_FIXES.md)** - Match acceptance modal and timer fixes

---

### [Setup](./setup/)
Installation, setup, and migration guides.

**Key Documents:**
- **[SETUP_INSTRUCTIONS.md](./setup/SETUP_INSTRUCTIONS.md)** - Complete setup guide
- **[MIGRATION_STEPS.md](./setup/MIGRATION_STEPS.md)** - Database and system migration steps
- [REDIS_SETUP_WINDOWS.md](./REDIS_SETUP_WINDOWS.md) - Redis installation for Windows
- [DEVELOPMENT_SETUP.md](./DEVELOPMENT_SETUP.md) - Development environment setup

---

### [Troubleshooting](./troubleshooting/)
Common issues, debugging guides, and quick fixes.

**Key Documents:**
- **[QUICK_FIX_REFERENCE.md](./troubleshooting/QUICK_FIX_REFERENCE.md)** ⭐ Quick reference for common fixes
- **[WEBSOCKET_PORT_REFERENCE.md](./troubleshooting/WEBSOCKET_PORT_REFERENCE.md)** - WebSocket port configuration
- **[DEADLOCK_ANALYSIS.md](./troubleshooting/DEADLOCK_ANALYSIS.md)** - Deadlock debugging and resolution
- [WEBSOCKET_CLEANUP_GUIDE.md](./troubleshooting/WEBSOCKET_CLEANUP_GUIDE.md) - WebSocket connection cleanup
- [DEBUG_EXPIRATION_ADDED.md](./troubleshooting/DEBUG_EXPIRATION_ADDED.md) - Match expiration debugging
- [LOGGING_ADDED.md](./troubleshooting/LOGGING_ADDED.md) - Logging system enhancements
- [FINAL_FIXES_SUMMARY.md](./troubleshooting/FINAL_FIXES_SUMMARY.md) - Summary of all fixes applied

---

## Quick Start Guides

### For Developers
1. **[DEVELOPMENT_SETUP.md](./DEVELOPMENT_SETUP.md)** - Set up your dev environment
2. **[QUICK_START.md](./QUICK_START.md)** - Get the system running
3. **[TESTING_GUIDE.md](./TESTING_GUIDE.md)** - Run tests and validate changes

### For System Architecture
1. **[ARCHITECTURE_IMPROVEMENTS.md](./ARCHITECTURE_IMPROVEMENTS.md)** - System architecture overview
2. **[IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)** - Feature roadmap
3. **[MATCH_ROOM_SPECIFICATION.md](./MATCH_ROOM_SPECIFICATION.md)** - Match room design

### For Operations
1. **[PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)** - Deploy to production
2. **[PROCESS_CLEANUP_FIX.md](./PROCESS_CLEANUP_FIX.md)** - Process management

---

## Project Status

- **[CURRENT_STATUS.md](./CURRENT_STATUS.md)** - Current project status and active features
- **[NEXT_STEPS.md](./NEXT_STEPS.md)** - Planned features and improvements

---

## Phase Documentation

Historical phase-based development documentation:

- [PHASE_1_LOBBY_SYSTEM_IMPLEMENTATION.md](./PHASE_1_LOBBY_SYSTEM_IMPLEMENTATION.md) - Lobby system foundation
- [PHASE_2_IMPLEMENTATION_SUMMARY.md](./PHASE_2_IMPLEMENTATION_SUMMARY.md) - Matchmaking implementation
- [PHASE_2_QUICKSTART.md](./PHASE_2_QUICKSTART.md) - Phase 2 quick start
- [PHASE_3_1_COMPLETION_SUMMARY.md](./PHASE_3_1_COMPLETION_SUMMARY.md) - Match flow completion
- [PHASE_3_IMPLEMENTATION_PLAN.md](./PHASE_3_IMPLEMENTATION_PLAN.md) - Advanced features plan

---

## Finding Documentation

### By Topic

- **Matchmaking Algorithm**: See [Matchmaking](./matchmaking/) folder
- **Testing & Bots**: See [Testing](./testing/) folder  
- **UI Issues**: See [Client UI](./client-ui/) folder
- **Setup Problems**: See [Setup](./setup/) and [Troubleshooting](./troubleshooting/) folders
- **WebSocket Issues**: See [Troubleshooting](./troubleshooting/) folder
- **Requeue Problems**: See [Matchmaking](./matchmaking/) folder (requeue documents)

### By File Type

- **System Design**: `ARCHITECTURE_*`, `IMPLEMENTATION_*`, `SPECIFICATION_*`
- **Bug Fixes**: `*_FIX*`, `*_FIXES_*`
- **Analysis**: `*_ANALYSIS*`, `*_REVIEW*`
- **Guides**: `*_GUIDE*`, `*_INSTRUCTIONS*`, `SETUP_*`, `QUICK_START*`
- **Status**: `*_STATUS*`, `*_SUMMARY*`, `*_COMPLETE*`

---

## System Components

### Backend (Django + Celery)
- **Matchmaking Service**: MMR-based matchmaking with time tolerance
- **Queue Manager**: Redis-based queue management
- **Match Confirmation**: 30-second acceptance flow with requeueing
- **Lobby Manager**: Party and solo lobby management
- **WebSocket Layer**: Real-time communication via Django Channels

### Frontend (Electron + React)
- **Queue UI**: Match finding and acceptance interface
- **Lobby UI**: Party management and preferences
- **Match UI**: In-game match tracking

### Infrastructure
- **Redis**: Caching, sessions, queues, and match state
- **PostgreSQL**: Persistent data storage
- **Celery**: Background task processing (matchmaking, cleanup)
- **Daphne**: ASGI server for WebSocket support

---

## Support

For issues or questions:
1. Check [TROUBLESHOOTING](./troubleshooting/) folder
2. Review [QUICK_FIX_REFERENCE.md](./troubleshooting/QUICK_FIX_REFERENCE.md)
3. See [CURRENT_STATUS.md](./CURRENT_STATUS.md) for known issues

---

**Last Updated**: October 2025  
**Version**: v2.0  
**Maintainers**: Scrim.GG Development Team
