import unicodedata
import re 

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





if __name__ == "__main__": 
    from src.user_interface.dunk_vision_controller import DunkVisionApp
    DunkVisionApp().mainloop()