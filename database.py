import json
import os
from datetime import datetime

from config import DB_FILE


def load_db() -> dict:
    """Charge la base de données JSON existante ou retourne une structure vide."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"alarmes": []}


def save_alarm(event_type: str) -> None:
    """Ajoute une entrée horodatée dans la base de données JSON."""
    db = load_db()
    now = datetime.now()
    entry = {
        "id":        len(db["alarmes"]) + 1,
        "type":      event_type,
        "date":      now.strftime("%Y-%m-%d"),
        "heure":     now.strftime("%H:%M:%S"),
        "timestamp": now.isoformat(),
    }
    db["alarmes"].append(entry)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)
    print(f"[DB] Alarme enregistrée : {entry}")
