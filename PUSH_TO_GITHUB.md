# Push to GitHub - Ready to Go!

Your repository is connected to: **https://github.com/malikc-ctg/JcQ.git**

## Quick Push Commands

```bash
cd /Users/malikcampbell/JcQ/jcq

# Configure git user (if not already done)
git config user.name "malikc-ctg"
git config user.email "your.email@example.com"  # Update with your email

# Commit all files
git commit -m "Initial commit: JcQ quantitative trading system

- Complete quantitative research and trading system for NQ/MNQ futures
- Feature engineering, probabilistic models, risk management
- Backtesting engine, walk-forward validation, Monte Carlo simulation
- Live trading loop with paper broker
- REST API for data ingestion
- Comprehensive test suite
- Supabase Postgres integration with SQLite fallback"

# Push to GitHub
git branch -M main
git push -u origin main
```

## What Will Be Pushed

✅ All source code (60+ Python modules)
✅ Configuration files (YAML configs)
✅ Database migrations
✅ Scripts (13 executable scripts)
✅ Tests (10 test files)
✅ Documentation (README, setup guides)
✅ CI/CD workflow
✅ License and project files

❌ **NOT pushed** (protected by .gitignore):
- `.env` file (contains secrets)
- Data files (Parquet, logs, models)
- Python cache files
- Virtual environment

## After Pushing

1. **Verify on GitHub**: Go to https://github.com/malikc-ctg/JcQ
2. **Check Actions**: GitHub Actions will run tests automatically
3. **Set up Secrets** (optional): For CI/CD with Supabase
   - Go to Settings > Secrets and variables > Actions
   - Add `SUPABASE_DB_URL` secret

## Troubleshooting

### Authentication Error
If you get authentication errors:
```bash
# Option 1: Use GitHub CLI
gh auth login
git push -u origin main

# Option 2: Use personal access token
# Generate token at: https://github.com/settings/tokens
# Use token as password when pushing
```

### Remote Already Exists
If you see "remote origin already exists":
```bash
git remote set-url origin https://github.com/malikc-ctg/JcQ.git
```

### Push Rejected
If push is rejected (empty remote):
```bash
git push -u origin main --force
# Be careful with --force, only use if remote is empty
```

## Next: Set Up Supabase

After pushing to GitHub, set up Supabase:

```bash
# Interactive setup
python scripts/setup_env.py

# Test connection
python scripts/test_supabase_connection.py

# Apply migrations
python scripts/apply_migrations.py
```

Your Supabase Project ID: **zqcbldgheimqrnqmbbed**

