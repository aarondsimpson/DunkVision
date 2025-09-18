from __future__ import annotations
import unicodedata, re, os, json
from pathlib import Path
from datetime import datetime
from typing import Any, TypedDict,Optional

_slug_rx = re.compile(r"[^a-z0-9]+")
_dash_rx = re.compile(r"-{2,}")

def slugify(text: str | None, *, default: str = "unnamed", maxlen: int = 80) -> str:
    if not text:
        return default
    s = unicodedata.normalize("NFKD", str(text))
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip()
    s = _slug_rx.sub("-", s)
    s = _dash_rx.sub("-", s).strip("-")
    if maxlen and len(s) > maxlen:
        s = s[:maxlen].rstrip("-")
    return s or default

def next_save_path(
        folder: str | Path, 
        *, 
        base: str = "game", 
        ext: str = ".json",
        width: int = 3, 
        start: int = 1, 
        create_dir: bool = False,
        timestamp_fallback: bool = True, 
        max_n: int = 9999, 
    ) -> Path:
        
        folder = Path(folder)
        if create_dir: 
             folder.mkdir(parents=True, exist_ok=True)
        
        if not ext.startswith("."):
             ext = f".{ext}"


        rx = re.compile(
            rf"^{re.escape(base)}_(\d{{{width},}}){re.escape(ext)}$",
            re.IGNORECASE
            )

        used: set[int] = set()
        if folder.exists():
            for p in folder.iterdir():
                if not p.is_file():
                    continue
                m = rx.match(p.name)
                if m:
                    try:
                        used.add(int(m.group(1)))
                    except ValueError:
                        pass

        if (folder / f"{base}{ext}").exists():
            used.add(1)
        
        n = start
        while n in used:
            n += 1

        if n > max_n and timestamp_fallback:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return folder / f"{base}_{stamp}{ext}"

        return folder / f"{base}_{str(n).zfill(width)}{ext}"

class DetectResult(TypedDict, total=False):
    ok: bool                         
    classification: str              
    reason: str                          
    safe_to_open_with_read_game: bool 
    path: str
    size: int
    ext: str
    is_json: bool
    schema: Optional[int]
    schema_name: Optional[str]
    header: dict                      
    suggested_ext: str                

def _peek_header(payload: Any) -> dict:
    header: dict[str, Any] = {}
    if isinstance(payload, dict):
        header["schema"] = payload.get("schema")
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        header["meta.schema_name"] = meta.get("schema_name")

        teams = payload.get("teams")
        if isinstance(teams, dict):
            names = teams.get("names")
            if isinstance(names, dict):
                header["teams.home"] = names.get("home")
                header["teams.away"] = names.get("away")

        game = payload.get("game")
        if isinstance(game, dict):
            header["game_date"] = game.get("game_date")
            header["game_location"] = game.get("game_location")

        ui = payload.get("ui")
        if isinstance(ui, dict):
            header["ui.mode"] = ui.get("mode")
            header["ui.quarter"] = ui.get("quarter")
    return {k: v for k, v in header.items() if v is not None}

def detect_game_file(path: str | Path, *, max_bytes: int = 20 * 1024 * 1024) -> DetectResult:
    p = Path(path)
    result: DetectResult = {
        "ok": False,
        "classification": "not_dunkvision",
        "reason": "",
        "safe_to_open_with_read_game": False,
        "path": str(p),
        "size": 0,
        "ext": "".join(p.suffixes).lower(),
        "is_json": False,
        "schema": None,
        "schema_name": None,
        "header": {},
        "suggested_ext": ".dvg.json",
    }

    if not p.exists():
        result["reason"] = "File does not exist."
        return result
    if not p.is_file():
        result["reason"] = "Not a regular file."
        return result

    try:
        size = p.stat().st_size
    except Exception:
        size = -1
    result["size"] = int(size) if size is not None else -1
    if size >= 0 and size > max_bytes:
        result["reason"] = f"File is too large for a save ({size} bytes)."
        return result

    try:
        with p.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        result["is_json"] = True
    except UnicodeDecodeError:
        result["reason"] = "Not UTF-8 text (likely binary, e.g., .docx)."
        return result
    except json.JSONDecodeError:
        result["reason"] = "Invalid JSON."
        return result
    except PermissionError:
        result["reason"] = "Permission denied."
        return result
    except OSError as e:
        result["reason"] = f"I/O error: {e}"
        return result


    schema = payload.get("schema") if isinstance(payload, dict) else None
    meta = payload.get("meta") if isinstance(payload, dict) else None
    schema_name = meta.get("schema_name") if isinstance(meta, dict) else None

    result["schema"] = schema if isinstance(schema, int) else None
    result["schema_name"] = schema_name if isinstance(schema_name, str) else None
    result["header"] = _peek_header(payload)

    if result["schema"] == 1 and result["schema_name"] == "dv-game":
        result["ok"] = True
        result["classification"] = "valid_dunkvision"
        result["safe_to_open_with_read_game"] = True

        ext = result["ext"] or ""
        if ext not in (".dvg.json",):
            result["suggested_ext"] = ".dvg.json"
        return result

    if isinstance(payload, dict):
        if payload.get("schema_version") == "dv_shots_v1" or "shots" in payload:
            result["reason"] = "JSON looks like an export dataset, not a game save."
            result["classification"] = "maybe_dunkvision"  
            return result

        result["reason"] = "JSON present but missing DunkVision game schema."
        result["classification"] = "not_dunkvision"
        return result

    result["reason"] = "Unrecognized file format."
    return result


def main():
    from src.user_interface.dunk_vision_controller import DunkVisionApp
    DunkVisionApp().mainloop()

if __name__ == "__main__":
    main()