# Development Setup Guide

## 🚀 Quick Start (Development)

### Prerequisites
- Python 3.8+
- Node.js 16+
- Redis
- PostgreSQL (or SQLite for development)
- Git

### 1. Clone Repository
```bash
git clone <repository-url>
cd scrimdotgg
```

### 2. Backend Setup
```bash
cd server
pipenv install
pipenv run python manage.py migrate
pipenv run python manage.py createsuperuser
```

### 3. Frontend Setup
```bash
cd client/frontend
npm install
```

### 4. Start Development Servers
```bash
# Terminal 1: Django Server
cd server
pipenv run python manage.py runserver

# Terminal 2: Celery Worker
cd server
pipenv run celery -A scrimgg worker --loglevel=info

# Terminal 3: Frontend
cd client/frontend
npm start
```

---

## 🔧 Detailed Setup

### Backend Dependencies
- Django 4.2+
- Django Channels
- Celery
- Redis
- PostgreSQL
- Python 3.8+

### Frontend Dependencies
- React 18+
- Electron
- Material-UI
- WebSocket client

### System Requirements
- Windows 10+ (for Valorant integration)
- 8GB RAM minimum
- 2GB free disk space

---

## 🐛 Troubleshooting

### Common Issues
1. **Port conflicts**: Change ports in settings
2. **Redis connection**: Ensure Redis is running
3. **Database errors**: Run migrations
4. **Frontend build**: Clear node_modules and reinstall

### Debug Mode
```bash
# Enable debug logging
export DEBUG=1
pipenv run python manage.py runserver --settings=scrimgg.settings.debug
```

---

## 📚 Additional Resources
- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://reactjs.org/)
- [Electron Documentation](https://electronjs.org/)
