
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json, os, time
from typing import Any

def _safe_write_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

@dataclass
class GameSave:
    schema: int
    saved_at: float
    meta: dict
    ui: dict
    teams: dict
    shots: list
    history: dict

def build_save_from_court(court) -> GameSave:
    # court == CourtFrame
    meta = {
        "app": "DunkVision",
        "schema_name": "dv-game",
        "version": 1,
    }
    ui = {
        "mode": court.mode,
        "quarter": court.quarter.get(),
        "selected_team_key": court.selected_team_key.get(),
        "scores": {"home": court.home_score.get(), "away": court.away_score.get()},
    }
    teams = {
        "order": list(court.team_order),
        "names": {k: v.get() for k, v in court.team_names.items()},
        "rosters": {k: list(v) for k, v in court.rosters.items()},
    }
    shots = list(court.data_points)  # already contains x,y,team,made,meta…
    history = {
        # Keep undo/redo so you can resume editing naturally.
        "actions": list(court.actions),
        "redo_stack": list(court.redo_stack),
    }
    return GameSave(
        schema=1,
        saved_at=time.time(),
        meta=meta,
        ui=ui,
        teams=teams,
        shots=shots,
        history=history,
    )

def write_game(path: Path, court) -> None:
    save = build_save_from_court(court)
    _safe_write_json(path, asdict(save))

def read_game(path: Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    # minimal forward-compat checks
    if data.get("schema") != 1 or data.get("meta", {}).get("schema_name") != "dv-game":
        raise ValueError("Unsupported game file.")
    return data
