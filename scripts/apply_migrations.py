#!/usr/bin/env python3
"""Apply database migrations."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jcq.core.logging import setup_logging, get_logger
from jcq.storage.db import get_engine, ensure_schema
from sqlalchemy import text

logger = get_logger(__name__)


def main():
    """Apply migrations."""
    setup_logging()
    logger.info("Applying database migrations...")
    
    engine = get_engine()
    
    # Read migration file
    migration_file = Path(__file__).parent.parent / "migrations" / "001_init.sql"
    
    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return 1
    
    with open(migration_file, "r") as f:
        sql = f.read()
    
    # Execute migration
    try:
        with engine.begin() as conn:
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            for stmt in statements:
                if stmt:
                    conn.execute(text(stmt))
        
        logger.info("Migrations applied successfully")
        return 0
    except Exception as e:
        logger.error(f"Failed to apply migrations: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

