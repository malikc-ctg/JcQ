"""Model version registry."""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from jcq.storage.db import get_engine
from jcq.storage.schema import RunRegistry
from sqlalchemy import text

logger = logging.getLogger(__name__)


def register_model_run(
    run_type: str,
    status: str = "running",
    meta: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Register a model run in the database.
    
    Args:
        run_type: Type of run (e.g., "train", "backtest", "walkforward")
        status: Status ("running", "completed", "failed")
        meta: Optional metadata dict
    
    Returns:
        Run ID
    """
    run_id = str(uuid.uuid4())
    engine = get_engine()
    
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO run_registry (run_id, run_type, started_at, status, meta)
                VALUES (:run_id, :run_type, :started_at, :status, :meta)
            """),
            {
                "run_id": run_id,
                "run_type": run_type,
                "started_at": datetime.utcnow(),
                "status": status,
                "meta": meta or {},
            },
        )
    
    logger.info(f"Registered run {run_id} ({run_type}, {status})")
    return run_id


def update_run_status(
    run_id: str,
    status: str,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """Update run status."""
    engine = get_engine()
    
    update_dict = {"status": status, "ended_at": datetime.utcnow()}
    if meta:
        update_dict["meta"] = meta
    
    with engine.begin() as conn:
        if "postgresql" in str(engine.url):
            from sqlalchemy.dialects.postgresql import json
            conn.execute(
                text("""
                    UPDATE run_registry
                    SET status = :status, ended_at = :ended_at,
                        meta = COALESCE(meta, '{}'::jsonb) || :meta::jsonb
                    WHERE run_id = :run_id
                """),
                {**update_dict, "run_id": run_id},
            )
        else:
            # SQLite
            import json as json_lib
            conn.execute(
                text("""
                    UPDATE run_registry
                    SET status = :status, ended_at = :ended_at
                    WHERE run_id = :run_id
                """),
                update_dict,
            )
    
    logger.info(f"Updated run {run_id} to {status}")

