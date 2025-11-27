from pathlib import Path
import json
import datetime


def load_json(path: str):
    """Safely load JSON from `path`. Returns parsed data or None on error."""
    try:
        p = Path(path)
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def now_iso():
    """Return current UTC time as ISO string (seconds resolution)."""
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat()


def ensure_db(db_path: str):
    p = Path(db_path)
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        # Create empty sqlite file or let the app create it later
        p.write_text("")
    return str(p)
