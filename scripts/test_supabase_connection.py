#!/usr/bin/env python3
"""Test Supabase connection."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jcq.core.logging import setup_logging, get_logger
from jcq.storage.db import get_engine, ensure_schema
from sqlalchemy import text

logger = get_logger(__name__)


def main():
    """Test Supabase connection."""
    setup_logging()
    
    db_url = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    
    if not db_url:
        logger.error("SUPABASE_DB_URL or DATABASE_URL not set in environment")
        logger.info("Please set it in your .env file")
        return 1
    
    logger.info("Testing Supabase connection...")
    logger.info(f"Database URL: {db_url.split('@')[0]}@[HIDDEN]")  # Hide password
    
    try:
        engine = get_engine()
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✅ Connected to PostgreSQL: {version[:50]}...")
        
        # Test schema
        logger.info("Checking schema...")
        ensure_schema()
        logger.info("✅ Schema verified")
        
        # Test a simple query
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
            table_count = result.scalar()
            logger.info(f"✅ Found {table_count} tables in public schema")
        
        logger.info("✅ Supabase connection successful!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        logger.info("\nTroubleshooting:")
        logger.info("1. Check your database password in .env file")
        logger.info("2. Verify SUPABASE_DB_URL format is correct")
        logger.info("3. Check Supabase Dashboard > Settings > Database")
        logger.info("4. Ensure your IP is allowed (if using IP restrictions)")
        return 1


if __name__ == "__main__":
    sys.exit(main())

