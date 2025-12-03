"""Optional Supabase Storage mirroring for Parquet files."""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_SUPABASE_CLIENT = None


def _get_supabase_client():
    """Lazy import and initialization of Supabase client."""
    global _SUPABASE_CLIENT
    
    if _SUPABASE_CLIENT is not None:
        return _SUPABASE_CLIENT
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.debug("Supabase Storage not configured (missing URL or key)")
        return None
    
    try:
        from supabase import create_client, Client
        _SUPABASE_CLIENT = create_client(supabase_url, supabase_key)
        logger.info("Supabase Storage client initialized")
        return _SUPABASE_CLIENT
    except ImportError:
        logger.debug("supabase-py not installed, skipping Storage mirroring")
        return None
    except Exception as e:
        logger.warning(f"Failed to initialize Supabase Storage: {e}")
        return None


def mirror_parquet_to_storage(
    local_path: str,
    storage_path: str,
    bucket: str = "quant-data",
) -> bool:
    """
    Mirror a Parquet file to Supabase Storage.
    
    Args:
        local_path: Local file path
        storage_path: Path in storage (under jcq/ prefix)
        bucket: Storage bucket name
    
    Returns:
        True if successful, False otherwise (no-op if not configured)
    """
    client = _get_supabase_client()
    if client is None:
        return False
    
    try:
        full_path = f"jcq/{storage_path}"
        
        with open(local_path, "rb") as f:
            client.storage.from_(bucket).upload(
                full_path,
                f.read(),
                file_options={"content-type": "application/octet-stream"},
            )
        
        logger.debug(f"Mirrored {local_path} to storage://{bucket}/{full_path}")
        return True
    except Exception as e:
        logger.warning(f"Failed to mirror to Supabase Storage: {e}")
        return False


def list_storage_files(prefix: str = "jcq/", bucket: str = "quant-data") -> list:
    """
    List files in Supabase Storage.
    
    Args:
        prefix: Path prefix
        bucket: Storage bucket name
    
    Returns:
        List of file paths (empty if not configured)
    """
    client = _get_supabase_client()
    if client is None:
        return []
    
    try:
        files = client.storage.from_(bucket).list(prefix)
        return [f["name"] for f in files]
    except Exception as e:
        logger.warning(f"Failed to list storage files: {e}")
        return []

