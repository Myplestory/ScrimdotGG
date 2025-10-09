# GitHub Setup Guide for Scrim.GG

## 📋 Prerequisites

1. **GitHub Account** - Create one at https://github.com
2. **Git Installed** - Check with `git --version`
3. **GitHub CLI (optional)** - Easier authentication: https://cli.github.com/

## 🚀 Method 1: Using GitHub CLI (Recommended)

### Step 1: Install GitHub CLI (if not installed)

**Windows:**
```bash
winget install --id GitHub.cli
```

Or download from: https://cli.github.com/

### Step 2: Authenticate with GitHub
```bash
gh auth login
```

Follow the prompts:
- Choose "GitHub.com"
- Choose "HTTPS"
- Authenticate via browser

### Step 3: Initialize and Push Repository
```bash
# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit - WebSocket refactor complete"

# Create GitHub repository and push
gh repo create scrimgg --public --source=. --remote=origin --push
```

**Done!** Your repository is now on GitHub at `https://github.com/yourusername/scrimgg`

---

## 🔧 Method 2: Manual Setup (Traditional)

### Step 1: Create Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `scrimgg`
3. Description: "Competitive Valorant matchmaking platform"
4. Choose **Public** or **Private**
5. **DO NOT** initialize with README, .gitignore, or license
6. Click "Create repository"

### Step 2: Initialize Local Repository

```bash
# Initialize git repository
git init

# Add all files
git add .

# Check what will be committed
git status

# Create initial commit
git commit -m "Initial commit - WebSocket refactor complete"
```

### Step 3: Connect to GitHub

Replace `yourusername` with your GitHub username:

```bash
# Add remote
git remote add origin https://github.com/yourusername/scrimgg.git

# Push to GitHub
git push -u origin main
```

**If you get an error about 'master' vs 'main':**
```bash
git branch -M main
git push -u origin main
```

---

## 🔐 Authentication Options

### Option A: HTTPS with Personal Access Token (Recommended)

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: "Scrim.GG Development"
4. Select scopes: `repo` (full control)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

When pushing, use:
- Username: Your GitHub username
- Password: The token (not your GitHub password)

### Option B: SSH Keys

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub at https://github.com/settings/ssh/new
```

Then use SSH URL:
```bash
git remote set-url origin git@github.com:yourusername/scrimgg.git
```

---

## 📝 What Gets Committed?

### ✅ Will Be Committed:
- Source code (`.py`, `.jsx`, `.js` files)
- Documentation (`.md` files)
- Configuration files (`package.json`, `Pipfile`)
- Examples directory
- Architecture documentation

### ❌ Will NOT Be Committed (in .gitignore):
- `node_modules/` - Dependencies (users run `npm install`)
- `__pycache__/` - Python bytecode
- `build/` - Build artifacts
- `dist/` - Distribution files
- `.env` - Environment variables
- `data/data.json` - User data
- `db.sqlite3` - Database files
- `Pipfile.lock` - Lock files
- `package-lock.json` - Lock files

---

## 🔍 Verify Everything

### Before Pushing, Check:

```bash
# See what will be committed
git status

# See file changes
git diff

# See commit log
git log
```

### Expected Output of `git status`:
```
On branch main
nothing to commit, working tree clean
```

---

## 📦 Repository Structure

Your GitHub repo will look like this:

```
scrimgg/
├── .gitignore                       # Git ignore rules
├── LICENSE                          # MIT License
├── README.md                        # Main documentation
├── ARCHITECTURE_IMPROVEMENTS.md     # System architecture
├── IMPLEMENTATION_ROADMAP.md        # Development plan
├── WEBSOCKET_REFACTOR_SUMMARY.md    # WebSocket details
├── QUICK_START.md                   # Quick start guide
├── REFACTOR_COMPLETE.md             # Refactor summary
├── GITHUB_SETUP.md                  # This file
├── examples/                        # Reference implementations
│   ├── 1_websocket_client_hook.jsx
│   ├── 2_improved_quart_backend.py
│   ├── 3_game_monitor_service.py
│   ├── 4_veto_system.py
│   ├── 5_match_coordinator.py
│   └── 6_enhanced_django_consumer.py
├── Scrim.GG_Client/                 # Desktop client
│   └── scrimgg/
│       ├── backend/                 # Python backend
│       └── frontend/                # React/Electron frontend
└── ScrimGG/                         # Django server
    └── scrimgg/
        ├── server/                  # Django app
        └── react-frontend/          # Web frontend (optional)
```

---

## 🎯 Post-Push Checklist

After pushing to GitHub:

- [ ] Visit your repository: `https://github.com/yourusername/scrimgg`
- [ ] Check README displays correctly
- [ ] Verify .gitignore is working (no `node_modules`, etc.)
- [ ] Add repository description
- [ ] Add topics/tags: `valorant`, `matchmaking`, `electron`, `django`, `websocket`
- [ ] Star your own repo (for visibility)
- [ ] Consider making it public (optional)

---

## 🔄 Future Updates

### To Push New Changes:

```bash
# Check what changed
git status

# Add specific files
git add path/to/file.js

# Or add all changes
git add .

# Commit with message
git commit -m "Add game state monitor"

# Push to GitHub
git push
```

### Create Branches for Features:

```bash
# Create and switch to new branch
git checkout -b feature/game-monitor

# Make changes, commit them
git add .
git commit -m "Implement game state monitoring"

# Push branch to GitHub
git push -u origin feature/game-monitor

# Create Pull Request on GitHub
# Merge when ready
```

---

## 🛡️ Best Practices

### Commit Messages:
- **Good:** `"Add WebSocket connection retry logic"`
- **Good:** `"Fix lobby chat message duplication"`
- **Good:** `"Refactor authentication flow for better error handling"`
- **Bad:** `"fix stuff"`
- **Bad:** `"update"`

### When to Commit:
- After completing a feature
- After fixing a bug
- Before starting major refactoring
- At the end of each work session

### Branch Naming:
- `feature/game-monitor` - New features
- `bugfix/chat-duplication` - Bug fixes
- `refactor/websocket-cleanup` - Code refactoring
- `docs/update-readme` - Documentation updates

---

## 🆘 Troubleshooting

### Error: "remote: Repository not found"
**Fix:** Check repository name and URL are correct
```bash
git remote -v
git remote set-url origin https://github.com/yourusername/scrimgg.git
```

### Error: "failed to push some refs"
**Fix:** Pull first, then push
```bash
git pull origin main --rebase
git push
```

### Error: "Permission denied (publickey)"
**Fix:** Use HTTPS instead of SSH, or set up SSH keys
```bash
git remote set-url origin https://github.com/yourusername/scrimgg.git
```

### Accidentally Committed Sensitive Files
**Fix:**
```bash
# Remove from git (keeps local copy)
git rm --cached path/to/sensitive/file

# Add to .gitignore
echo "path/to/sensitive/file" >> .gitignore

# Commit removal
git commit -m "Remove sensitive file from tracking"
git push
```

### Want to Start Over
```bash
# Remove git history
rm -rf .git

# Start fresh
git init
git add .
git commit -m "Initial commit"
```

---

## 📊 Repository Settings (on GitHub)

After creating the repo, configure:

### General Settings:
- Description: "Competitive Valorant matchmaking platform"
- Website: Your deployment URL (if any)
- Topics: `valorant`, `matchmaking`, `faceit`, `electron`, `django`, `websocket`, `gaming`

### Features:
- ✅ Issues (for bug tracking)
- ✅ Discussions (for community)
- ❌ Wiki (not needed yet)
- ❌ Projects (not needed yet)

### Branches:
- Default branch: `main`
- Branch protection: Enable for `main` (prevents force push)

---

## 🎉 You're Done!

Your code is now safely on GitHub! 

**Next steps:**
1. Share the repository URL with collaborators
2. Continue development (see `IMPLEMENTATION_ROADMAP.md`)
3. Keep pushing updates regularly
4. Consider adding CI/CD (GitHub Actions)

**Repository URL:** `https://github.com/yourusername/scrimgg`

---

## 📞 Need Help?

- GitHub Docs: https://docs.github.com
- Git Basics: https://git-scm.com/book/en/v2
- Git Cheat Sheet: https://education.github.com/git-cheat-sheet-education.pdf


