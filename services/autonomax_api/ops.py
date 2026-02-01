from __future__ import annotations

from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import OpsLock
from .settings import settings

def _now():
    return datetime.now(timezone.utc)

def acquire_lock(db: Session, name: str) -> bool:
    ttl = timedelta(seconds=settings.ops_lock_ttl_seconds)
    until = _now() + ttl

    row = db.execute(select(OpsLock).where(OpsLock.name == name)).scalar_one_or_none()
    if row is None:
        row = OpsLock(name=name, locked_until=until)
        db.add(row)
        db.commit()
        return True

    # If still locked, deny
    if row.locked_until and row.locked_until > _now():
        return False

    row.locked_until = until
    db.commit()
    return True
