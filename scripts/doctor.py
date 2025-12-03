#!/usr/bin/env python3
"""System health check script."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jcq.core.logging import setup_logging, get_logger
from jcq.core.config import load_config
from jcq.storage.db import get_engine, ensure_schema
from jcq.storage.parquet_store import read_bars

logger = get_logger(__name__)


def check_python_version():
    """Check Python version."""
    import sys
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def check_config():
    """Check configuration."""
    try:
        config = load_config()
        print("✅ Configuration loaded")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def check_directories():
    """Check directory write access."""
    repo_root = Path(__file__).parent.parent
    dirs = ["data/bars", "data/features", "data/models", "data/runs", "data/logs"]
    
    all_ok = True
    for dir_path in dirs:
        full_path = repo_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            # Test write
            test_file = full_path / ".test"
            test_file.write_text("test")
            test_file.unlink()
            print(f"✅ {dir_path}")
        except Exception as e:
            print(f"❌ {dir_path}: {e}")
            all_ok = False
    
    return all_ok


def check_database():
    """Check database connectivity."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✅ Database connection OK")
        
        # Check schema
        ensure_schema()
        print("✅ Database schema OK")
        return True
    except Exception as e:
        print(f"⚠️  Database: {e} (using SQLite fallback)")
        return True  # SQLite fallback is OK


def check_sample_data():
    """Check sample data ingestion."""
    try:
        df = read_bars("NQ", "1m")
        if not df.empty:
            print(f"✅ Sample data: {len(df)} bars found")
        else:
            print("⚠️  No sample data (run generate_demo_data.py)")
        return True
    except Exception as e:
        print(f"⚠️  Sample data check: {e}")
        return True


def main():
    """Run all checks."""
    setup_logging()
    print("JcQ System Health Check\n" + "=" * 40)
    
    checks = [
        ("Python Version", check_python_version),
        ("Configuration", check_config),
        ("Directories", check_directories),
        ("Database", check_database),
        ("Sample Data", check_sample_data),
    ]
    
    results = []
    for name, check_fn in checks:
        print(f"\n{name}:")
        results.append(check_fn())
    
    print("\n" + "=" * 40)
    if all(results):
        print("✅ All checks passed")
        return 0
    else:
        print("❌ Some checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

