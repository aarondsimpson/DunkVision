from src.user_interface.dunk_vision_controller import DunkVisionApp

def slugify(text: str) -> str: 
    import re 
    s = (text or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "unnamed"


if __name__ == "__main__": 
    DunkVisionApp().mainloop()