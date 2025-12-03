#!/usr/bin/env python3
"""Interactive setup script for .env file."""

import sys
from pathlib import Path
import getpass

def main():
    """Interactive .env setup."""
    env_file = Path(__file__).parent.parent / ".env"
    
    if env_file.exists():
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing .env file")
            return 0
    
    print("\n=== JcQ Environment Setup ===\n")
    
    # Supabase configuration
    print("Supabase Configuration:")
    print("Project URL: https://zqcbldgheimqrnqmbbed.supabase.co")
    print("Get your database password from: Supabase Dashboard > Settings > Database\n")
    
    db_password = getpass.getpass("Enter your Supabase database password: ")
    
    if not db_password:
        print("⚠️  No password entered. You'll need to set SUPABASE_DB_URL manually.")
        db_url = ""
    else:
        # Use pooler connection (recommended)
        db_url = f"postgresql://postgres.zqcbldgheimqrnqmbbed:{db_password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    
    # Service role key (already known)
    service_role_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpxY2JsZGdoZWltcXJucW1iYmVkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDcwMzk2MiwiZXhwIjoyMDc2Mjc5OTYyfQ.qRTk5aTno8CYASO6Eu9VU9GTh6ZyV1FYgmn2r7Uv3E0"
    
    # FRED API key (optional)
    print("\nFRED API Key (optional):")
    print("Get a free key from: https://fred.stlouisfed.org/docs/api/api_key.html")
    fred_key = input("Enter FRED API key (or press Enter to skip): ").strip()
    
    # Execution enabled
    print("\nExecution Control:")
    exec_enabled = input("Enable execution? (y/N): ").strip().lower() == 'y'
    
    # Log level
    print("\nLogging Level:")
    log_level = input("Enter log level (DEBUG/INFO/WARNING/ERROR/CRITICAL) [INFO]: ").strip() or "INFO"
    
    # Write .env file
    env_content = f"""# Database Configuration
# Supabase Postgres connection string
SUPABASE_DB_URL={db_url}

# Supabase Storage (Optional - for mirroring Parquet files)
SUPABASE_URL=https://zqcbldgheimqrnqmbbed.supabase.co
SUPABASE_SERVICE_ROLE_KEY={service_role_key}

# Federal Reserve Economic Data API (Optional)
"""
    
    if fred_key:
        env_content += f"FRED_API_KEY={fred_key}\n"
    else:
        env_content += "# FRED_API_KEY=your_fred_api_key_here\n"
    
    env_content += f"""
# Execution Control
# MUST be explicitly set to "true" to enable any trading execution
EXECUTION_ENABLED={'true' if exec_enabled else 'false'}

# Logging
LOG_LEVEL={log_level}
"""
    
    env_file.parent.mkdir(parents=True, exist_ok=True)
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print(f"\n✅ Created .env file at {env_file}")
    print("\nNext steps:")
    print("1. Test connection: python scripts/test_supabase_connection.py")
    print("2. Apply migrations: python scripts/apply_migrations.py")
    print("3. Run doctor: python scripts/doctor.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

