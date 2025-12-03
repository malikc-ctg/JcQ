# GitHub Setup Instructions

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `JcQ` (or your preferred name)
3. Description: "Quantitative research and trading system for NQ/MNQ futures"
4. Choose Public or Private
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## Step 2: Connect Local Repository to GitHub

Run these commands in the `jcq` directory:

```bash
cd /Users/malikcampbell/JcQ/jcq

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: JcQ quantitative trading system"

# Add GitHub remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/JcQ.git

# Or if using SSH:
# git remote add origin git@github.com:YOUR_USERNAME/JcQ.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Set Up GitHub Secrets (for CI/CD)

If you want to use GitHub Actions with Supabase:

1. Go to your repository on GitHub
2. Settings > Secrets and variables > Actions
3. Add these secrets:
   - `SUPABASE_DB_URL`: Your Supabase database connection string
   - `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key

## Step 4: Verify Connection

```bash
git remote -v  # Should show your GitHub remote
git status     # Check repository status
```

## Troubleshooting

- If you get authentication errors, set up SSH keys or use GitHub CLI
- If push fails, make sure the remote URL is correct
- For private repos, ensure you have proper access tokens

