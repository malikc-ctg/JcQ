# GitHub Actions Setup

If you want to run CI/CD tests with Supabase, you'll need to configure GitHub Secrets.

## Setting Up GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Add these secrets:

### Required Secrets

- **Name**: `SUPABASE_DB_URL`
  - **Value**: Your full Supabase database connection string
  - Example: `postgresql://postgres.zqcbldgheimqrnqmbbed:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres`

- **Name**: `SUPABASE_SERVICE_ROLE_KEY` (optional, for storage tests)
  - **Value**: Your Supabase service role key
  - Found in: Supabase Dashboard > Settings > API

## Updating CI Workflow

The current CI workflow (`ci.yml`) runs tests without database. To enable database tests:

1. Edit `.github/workflows/ci.yml`
2. Add environment variables to the test step:

```yaml
- name: Run tests
  run: |
    pytest tests/ -v --tb=short
  env:
    PYTHONPATH: src
    SUPABASE_DB_URL: ${{ secrets.SUPABASE_DB_URL }}
```

## Note

Database tests are marked to skip if `SUPABASE_DB_URL` is not set, so the CI will work even without secrets configured.

