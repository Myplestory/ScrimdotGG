# GitHub Setup Guide for Scrim.GG

## 📋 Prerequisites

1. **GitHub Account** - Create one at https://github.com
2. **Git Installed** - Download from https://git-scm.com/
3. **Code Editor** - VS Code recommended

## 🚀 Quick Setup

### 1. Fork the Repository
1. Go to the main Scrim.GG repository
2. Click "Fork" button
3. Select your account as destination

### 2. Clone Your Fork
```bash
git clone https://github.com/YOUR_USERNAME/scrimdotgg.git
cd scrimdotgg
```

### 3. Add Upstream Remote
```bash
git remote add upstream https://github.com/ORIGINAL_OWNER/scrimdotgg.git
```

### 4. Verify Setup
```bash
git remote -v
# Should show:
# origin    https://github.com/YOUR_USERNAME/scrimdotgg.git (fetch)
# origin    https://github.com/YOUR_USERNAME/scrimdotgg.git (push)
# upstream  https://github.com/ORIGINAL_OWNER/scrimdotgg.git (fetch)
# upstream  https://github.com/ORIGINAL_OWNER/scrimdotgg.git (push)
```

---

## 🔄 Workflow

### Daily Workflow
```bash
# 1. Fetch latest changes
git fetch upstream

# 2. Switch to main branch
git checkout main

# 3. Merge upstream changes
git merge upstream/main

# 4. Push to your fork
git push origin main
```

### Feature Development
```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes and commit
git add .
git commit -m "Add your feature"

# 3. Push to your fork
git push origin feature/your-feature-name

# 4. Create Pull Request on GitHub
```

---

## 📝 Commit Guidelines

### Commit Message Format
```
type(scope): description

[optional body]

[optional footer]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

### Examples
```
feat(auth): add OAuth2 integration
fix(matchmaking): resolve team balance bug
docs(readme): update installation guide
refactor(backend): modularize bootstrap.py
```

---

## 🔍 Code Review Process

### Before Submitting PR
1. **Run Tests**: Ensure all tests pass
2. **Code Quality**: Follow style guidelines
3. **Documentation**: Update relevant docs
4. **Screenshots**: For UI changes

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Manual testing completed
- [ ] Screenshots attached (if UI changes)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or noted)
```

---

## 🛠️ Development Tools

### VS Code Extensions
- Python
- JavaScript/TypeScript
- GitLens
- Prettier
- ESLint

### Git Hooks
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Environment Setup
```bash
# Create .env file
cp .env.example .env
# Edit .env with your settings
```

---

## 📞 Support

### Common Issues
1. **Merge Conflicts**: Use VS Code merge tool
2. **Authentication**: Use GitHub CLI or SSH keys
3. **Branch Protection**: Contact maintainers

### Resources
- [Git Documentation](https://git-scm.com/docs)
- [GitHub Docs](https://docs.github.com/)
- [VS Code Git](https://code.visualstudio.com/docs/versioncontrol/git)

---

## 🎯 Best Practices

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring

### File Organization
- Keep related files together
- Use descriptive names
- Follow existing patterns
- Document complex logic

### Code Quality
- Write clean, readable code
- Add comments for complex logic
- Follow existing style
- Test your changes

---

**Happy coding! 🚀**
