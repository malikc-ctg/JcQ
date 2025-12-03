# Supabase Setup Instructions

## Step 1: Get Your Database Password

1. Go to https://supabase.com/dashboard
2. Select your project: `zqcbldgheimqrnqmbbed`
3. Go to **Settings** > **Database**
4. Find your database password (or reset it if needed)
5. Copy the password

## Step 2: Update .env File

Edit `.env` and replace `[YOUR_PASSWORD]` with your actual database password:

```bash
# Option 1: Using Supabase Pooler (recommended for connection pooling)
SUPABASE_DB_URL=postgresql://postgres.zqcbldgheimqrnqmbbed:YOUR_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# Option 2: Direct connection (if pooler doesn't work)
SUPABASE_DB_URL=postgresql://postgres.zqcbldgheimqrnqmbbed:YOUR_PASSWORD@db.zqcbldgheimqrnqmbbed.supabase.co:5432/postgres
```

## Step 3: Test Connection

Run the doctor script to verify everything works:

```bash
python scripts/doctor.py
```

This will:
- Check Python version
- Validate configuration
- Test database connectivity
- Verify schema

## Step 4: Apply Migrations

Apply the database schema:

```bash
python scripts/apply_migrations.py
```

This creates all necessary tables:
- `market_bars`
- `features_store`
- `model_outputs`
- `trade_log`
- `sim_runs`
- `macro_series`
- `run_registry`

## Step 5: Verify in Supabase Dashboard

1. Go to **Table Editor** in Supabase Dashboard
2. You should see all 7 tables created
3. Check that indexes are created properly

## Connection String Formats

### Pooler (Recommended)
```
postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### Direct Connection
```
postgresql://postgres.[PROJECT_REF]:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

### Using Connection Pooling
The pooler (port 6543) is recommended for applications as it:
- Handles connection pooling automatically
- Reduces connection overhead
- Better for concurrent requests

## Troubleshooting

### Connection Refused
- Check that your IP is allowed in Supabase Dashboard > Settings > Database > Connection Pooling
- Verify password is correct
- Try direct connection instead of pooler

### Authentication Failed
- Double-check password (no extra spaces)
- Ensure you're using the correct project reference
- Try resetting the database password

### SSL Required
- Supabase requires SSL by default
- The connection string should work as-is
- If issues persist, add `?sslmode=require` to connection string

## Optional: Supabase Storage Setup

If you want to mirror Parquet files to Supabase Storage:

1. Go to **Storage** in Supabase Dashboard
2. Create a bucket named `quant-data` (or update config)
3. Set bucket to **Public** if you want public access
4. The `.env` file already has `SUPABASE_SERVICE_ROLE_KEY` configured

## Security Notes

- **Never commit `.env` file to git** (it's in .gitignore)
- Keep your database password secure
- Service role key has full access - keep it secret
- Use connection pooling in production
- Consider using Supabase's connection string builder in dashboard

