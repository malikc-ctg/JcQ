# Quick Start: Connect GitHub & Supabase

## 1. Set Up Supabase Connection

### Option A: Interactive Setup (Recommended)
```bash
cd /Users/malikcampbell/JcQ/jcq
python scripts/setup_env.py
```

This will:
- Prompt for your Supabase database password
- Create `.env` file with all configuration
- Set up connection strings

### Option B: Manual Setup
1. Get your database password from Supabase Dashboard > Settings > Database
2. Create `.env` file:
```bash
cp .env.example .env
# Edit .env and replace [YOUR_PASSWORD] with your actual password
```

### Test Connection
```bash
python scripts/test_supabase_connection.py
```

### Apply Database Schema
```bash
python scripts/apply_migrations.py
```

## 2. Set Up GitHub Repository

### Step 1: Create Repository on GitHub
1. Go to https://github.com/new
2. Repository name: `JcQ`
3. **DO NOT** initialize with README/gitignore (we have them)
4. Click "Create repository"

### Step 2: Connect Local Repository
```bash
cd /Users/malikcampbell/JcQ/jcq

# Configure git (if not already done)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Initialize and commit
git add .
git commit -m "Initial commit: JcQ quantitative trading system"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/JcQ.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 3: Verify
```bash
git remote -v  # Should show your GitHub remote
```

## 3. Verify Everything Works

```bash
# Run system health check
python scripts/doctor.py

# Should show:
# ✅ Python version
# ✅ Configuration loaded
# ✅ Directories OK
# ✅ Database connection OK
# ✅ Schema OK
```

## 4. Optional: Set Up GitHub Secrets (for CI/CD)

If you want GitHub Actions to run database tests:

1. Go to your GitHub repo > Settings > Secrets and variables > Actions
2. Add secret: `SUPABASE_DB_URL` with your full connection string
3. Add secret: `SUPABASE_SERVICE_ROLE_KEY` (already in your .env)

## Troubleshooting

### Supabase Connection Issues
- Verify password is correct (no extra spaces)
- Check Supabase Dashboard > Settings > Database
- Try direct connection instead of pooler
- See `SETUP_SUPABASE.md` for detailed help

### GitHub Push Issues
- Make sure you're authenticated (SSH keys or GitHub CLI)
- Verify remote URL is correct
- Check you have write access to the repository

### Need Help?
- See `SETUP_GITHUB.md` for detailed GitHub setup
- See `SETUP_SUPABASE.md` for detailed Supabase setup
- Run `python scripts/doctor.py` for system diagnostics

