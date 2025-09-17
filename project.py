from __future__ import annotations
import unicodedata
import re 
from pathlib import Path
from datetime import datetime

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

        rx = re.compile(rf"^{re.escape(base)}_(\d{{{width},}}){re.escape(ext)}$")

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

        n = start
        while n in used:
            n += 1

        if n > max_n and timestamp_fallback:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return folder / f"{base}_{stamp}{ext}"

        return folder / f"{base}_{str(n).zfill(width)}{ext}"



def main():
    from src.user_interface.dunk_vision_controller import DunkVisionApp
    DunkVisionApp().mainloop()

if __name__ == "__main__":
    main()