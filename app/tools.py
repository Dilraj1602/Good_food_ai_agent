"""Whitelisted tools used by the controller. Keeps all DB operations here and
exposes a small set of functions the controller may call.
"""

import os
import uuid
import sqlite3
from typing import List, Dict, Any, Optional
from app.utils import load_json, now_iso, ensure_db


ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(ROOT, "data", "restaurants_seed.json")
DB_PATH = os.path.join(ROOT, "db", "reservations.db")


def _ensure_db_conn() -> sqlite3.Connection:
    ensure_db(DB_PATH)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reservations (
            id TEXT PRIMARY KEY,
            restaurant_id TEXT,
            restaurant_name TEXT,
            datetime TEXT,
            party_size INTEGER,
            name TEXT,
            contact TEXT,
            status TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    return conn


def load_restaurants() -> List[Dict[str, Any]]:
    data = load_json(DATA_PATH)
    if data:
        return data
    # fallback single restaurant
    return [
        {
            "id": "r_000",
            "name": "GoodFoods Default",
            "area": "Koramangala",
            "capacity": 40,
            "cuisines": ["Indian"],
            "rating": 4.2,
            "tables": [{"table_id": "T1", "seats": 4}],
            "open_hours": {"mon": "11:00-23:00"},
        }
    ]


def search_locations(area: str = "", party_size: int = 2, vibe: str = "", limit: int = 3) -> List[Dict[str, Any]]:
    restaurants = load_restaurants()
    area_lower = (area or "").strip().lower()
    results: List[Dict[str, Any]] = []
    for r in restaurants:
        if area_lower and area_lower not in (r.get("area", "") or "").lower():
            continue
        if int(r.get("capacity", 0) or 0) < int(party_size or 0):
            continue
        score = float(r.get("rating", 3.0) or 3.0)
        rcopy = dict(r)
        rcopy["_score"] = score
        results.append(rcopy)
    results = sorted(results, key=lambda x: x.get("_score", 0), reverse=True)
    return results[: int(limit or 3)]


def check_availability(restaurant_id: str, datetime_iso: str, party_size: int) -> Dict[str, Any]:
    conn = _ensure_db_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT SUM(party_size) FROM reservations WHERE restaurant_id=? AND datetime=? AND status='CONFIRMED'",
        (restaurant_id, datetime_iso),
    )
    row = cur.fetchone()
    used = int(row[0] or 0)
    restaurants = load_restaurants()
    r = next((x for x in restaurants if str(x.get("id")) == str(restaurant_id)), None)
    capacity = int(r.get("capacity", 0) or 0) if r else 0
    available = (used + int(party_size or 0)) <= capacity
    return {"restaurant_id": restaurant_id, "available": available, "used": used, "capacity": capacity}


def create_reservation(restaurant_id: str, restaurant_name: str, datetime_iso: str, party_size: int, name: str, contact: str) -> Dict[str, Any]:
    conn = _ensure_db_conn()
    cur = conn.cursor()
    av = check_availability(restaurant_id, datetime_iso, party_size)
    if not av.get("available"):
        return {"success": False, "reason": "NO_AVAILABILITY", "used": av.get("used"), "capacity": av.get("capacity")}
    rid = str(uuid.uuid4())[:8]
    created_at = now_iso()
    cur.execute(
        "INSERT INTO reservations (id, restaurant_id, restaurant_name, datetime, party_size, name, contact, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (rid, restaurant_id, restaurant_name, datetime_iso, int(party_size or 0), name or "Guest", contact or "N/A", "CONFIRMED", created_at),
    )
    conn.commit()
    return {"success": True, "id": rid, "restaurant_name": restaurant_name, "datetime": datetime_iso, "party_size": party_size, "contact": contact}


def modify_reservation(booking_id: str, new_datetime: Optional[str] = None, new_party_size: Optional[int] = None) -> Dict[str, Any]:
    conn = _ensure_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT restaurant_id, restaurant_name, datetime, party_size FROM reservations WHERE id=? AND status='CONFIRMED'", (booking_id,))
    row = cur.fetchone()
    if not row:
        return {"success": False, "reason": "NOT_FOUND"}
    restaurant_id, restaurant_name, old_datetime, old_party = row
    ndt = new_datetime or old_datetime
    nps = int(new_party_size or old_party)
    av = check_availability(restaurant_id, ndt, nps)
    if not av.get("available"):
        return {"success": False, "reason": "NO_AVAILABILITY"}
    cur.execute("UPDATE reservations SET datetime=?, party_size=? WHERE id=?", (ndt, nps, booking_id))
    conn.commit()
    return {"success": True, "id": booking_id, "restaurant_name": restaurant_name, "datetime": ndt, "party_size": nps}


def cancel_reservation(booking_id: str) -> Dict[str, Any]:
    conn = _ensure_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT status FROM reservations WHERE id=?", (booking_id,))
    row = cur.fetchone()
    if not row:
        return {"success": False, "reason": "NOT_FOUND"}
    cur.execute("UPDATE reservations SET status='CANCELLED' WHERE id=?", (booking_id,))
    conn.commit()
    return {"success": True, "id": booking_id, "status": "CANCELLED"}


def send_notification(method: str, dest: str, message: str) -> Dict[str, Any]:
    # placeholder for integration
    print(f"[NOTIFY] {method} -> {dest}: {message}")
    return {"sent": True, "method": method, "dest": dest}
