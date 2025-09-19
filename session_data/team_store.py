from __future__ import annotations
import json, os, time, uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Tuple

from src import config 


SCHEMA_VERSION = 1
DEFAULT_ROSTER = ["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"]

DEFAULT_TEAMS: List[Tuple[str, str]] = [
    ("t_default_home", "My Team"),
    ("t_default_away", "Their Team")
]

TEAMS_DB_PATH: Path = config.SESSION_DATA_DIR / "teams.json"
TMP_DIR: Path = config.TMP_DIR

LEGACY_STORE_PATH: Path = Path(__file__).resolve().parent / "custom_team.json"

@dataclass
class Team: 
    team_id: str
    team_name: str
    roster: List[str]
    updated_at: str
    version: int = 1

    @staticmethod
    def new(name: str, roster: Optional[List[str]] = None) -> "Team":
        rid = f"t_{uuid.uuid4().hex[:8]}"
        return Team(
            team_id=rid,
            team_name=name,
            roster=list(roster or DEFAULT_ROSTER),
            updated_at=_now(),
            version=1,
        )
def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def _safe_write_json(path: Path, payload: dict) -> None: 
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    tmp = TMP_DIR / f"{path.name}.tmp"
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp,path)

def _empty_store() -> dict: 
    return {"schema": SCHEMA_VERSION, "teams": []}

def _ensure_defaults(store: dict) -> dict: 
    existing_ids = {t.get("team_id") for t in store.get("teams", [])}
    changed = False 
    for tid, name in DEFAULT_TEAMS: 
        if tid not in existing_ids: 
            store["teams"].append(asdict(Team(
                team_id=tid, 
                team_name=name, 
                roster=list(DEFAULT_ROSTER),
                updated_at = _now(),
                version=1,
            )))
            changed = True
    if changed: 
        _safe_write_json(TEAMS_DB_PATH, store)
    return store 

def _upgrade_if_needed(store: dict) -> dict:
    if store.get("schema") != SCHEMA_VERSION:
        store["schema"] = SCHEMA_VERSION
        _safe_write_json(TEAMS_DB_PATH, store)
    return store

def _migrate_if_needed() -> None: 
    if TEAMS_DB_PATH.exists():
        return 
    if LEGACY_STORE_PATH.exists():
        try:
            data = json.loads(LEGACY_STORE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                _safe_write_json(TEAMS_DB_PATH, data)
                return
        except Exception:
            pass
    _safe_write_json(TEAMS_DB_PATH, _empty_store())

def load_store() -> dict:
    _migrate_if_needed()
    try:
        store = json.loads(TEAMS_DB_PATH.read_text(encoding="utf-8"))
    except Exception:
        store = _empty_store()
        _safe_write_json(TEAMS_DB_PATH, store)

    store = _upgrade_if_needed(store)
    store = _ensure_defaults(store)
    if "teams" not in store:
        store["teams"] = []
    return store

def list_teams() -> List[Team]:
    store = load_store()
    return [Team(**t) for t in store.get("teams", [])]

def get_team_by_id(team_id: str) -> Optional[Team]:
    for t in list_teams():
        if t.team_id == team_id:
            return t
    return None 

def get_team_by_name(name: str) -> Optional[Team]:
    name_norm = (name or "").strip().lower()
    for t in list_teams():
        if t.team_name.strip().lower() == name_norm:
            return t
    return None 

def upsert_team(*, team_name: str, roster: List[str], team_id: Optional[str] = None) -> Team:
    store = load_store()
    teams = store["teams"]

    idx = None
    if team_id: 
        for i, t in enumerate(teams):
            if t.get("team_id") == team_id:
                idx = i 
                break 
    if idx is None: 
        for i, t in enumerate(teams):
            if t.get("team_name", "").strip().lower() == team_name.strip().lower():
                idx = i 
                break 

    if idx is None: 
        t = Team.new(team_name, roster)
    else: 
        t = Team(**teams[idx])
        t.team_name = team_name
        t.roster = list(roster)
        t.version += 1
        t.updated_at = _now()

    if idx is None: 
        teams.append(asdict(t))
    else: 
        teams[idx] = asdict(t)

    _safe_write_json(TEAMS_DB_PATH, store)
    return t

def rename_team(team_id: str, new_name: str) -> Optional[Team]:
    t = get_team_by_id(team_id)
    if not t: 
        return None     
    return upsert_team(team_id=team_id, team_name=new_name, roster=t.roster)

def set_roster(team_id: str, roster: List[str]) -> Optional[Team]:
    t = get_team_by_id(team_id)
    if not t: 
        return None
    return upsert_team(team_id=team_id, team_name=t.team_name, roster=roster)

def delete_team(team_id: str) -> bool: 
    store = load_store()
    teams = store["teams"]
    new_teams = [t for t in teams if t.get("team_id") != team_id]
    if len(new_teams) == len(teams):
        return False
    store["teams"] = new_teams
    _safe_write_json(TEAMS_DB_PATH, store)
    return True

