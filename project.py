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

def _looks_like_text(b: bytes) -> bool:
    head = b[:4096]
    binary_magics = (
        b"\x50\x4B\x03\x04",  # ZIP (docx, xlsx, etc.)
        b"%PDF",              # PDF
        b"\x89PNG",           # PNG
        b"\xFF\xD8\xFF",      # JPEG
    )
    if b"\x00" in head:
        return False
    if any(head.startswith(m) for m in binary_magics):
        return False

    ctrl = sum(1 for c in head if c < 32 and c not in (9, 10, 13))
    return ctrl <= 2


def detect_game_file(path):
    p = Path(path)
    ext = "".join(p.suffixes).lower()

    out = {
        "ok": False,
        "classification": "not_dunkvision",
        "ext": ext,
        "reason": "",
        "safe_to_open_with_read_game": False,
    }

    if not p.exists():
        out["reason"] = "File does not exist."
        return out
    if p.is_dir():
        out["reason"] = "Path is a directory, not a file."
        return out
    
    try:
        raw = p.read_bytes()
    except Exception as e:
        out["reason"] = f"File not readable: {e}"
        return out

    if not _looks_like_text(raw):
        out["reason"] = "Not UTF-8 text."
        return out

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        out["reason"] = "Not UTF-8 text."
        return out

    try:
        data = json.loads(text)
    except Exception:
        out["reason"] = "Invalid JSON."
        return out

    schema = data.get("schema")
    schema_name = (data.get("meta") or {}).get("schema_name")
    if schema == 1 and schema_name == "dv-game":
        out.update({
            "ok": True,
            "classification": "valid_dunkvision",
            "safe_to_open_with_read_game": True,
            "schema": schema,
            "schema_name": schema_name,
            "reason": "",
        })
        return out

    if (data.get("schema_version") == "dv_shots_v1") or ("shots" in data and "ui" in data and "teams" in data):
        out.update({
            "ok": False,
            "classification": "maybe_dunkvision",
            "reason": "Looks like a DunkVision export, not a game save.",
        })
        return out

    out["reason"] = "Unrecognized file."
    return out


def main():
    from src.user_interface.dunk_vision_controller import DunkVisionApp
    DunkVisionApp().mainloop()

if __name__ == "__main__":
    main()