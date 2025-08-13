from __future__ import annotations
from tkinter import messagebox, Toplevel, ttk, StringVar, Misc, Entry, Frame

MESSAGES = dict[str, dict[str, str]] = {
    "quit": {
        "title": "Quit", 
        "message": "Unsaved work will be lost. Quit?"
    },
    "confirm_home": {
        "title": "Return Home?",
        "message": "Unsaved work will be lost. Return home?"
    },
    "confirm_reset": {
        "title": "Reset Game?",
        "message": "Reset the Court"
    },
    "confirm_end": {
        "title": "End Game?",
        "message": "End the Game?"
    },
    "confirm_remove_player": {
        "title": "Remove Player?",
        "message": "Remove {name} from {team}?"
    },
}
#Will add more as they appear
#Will add "load" section for load-related messages
#Will add "save" section for save-related messages 

def resolve(key_or_title: str, message: str | None, **fmt) -> tuple[str, str]:
    if message is None and key_or_title in MESSAGES:
        m = MESSAGES[key_or_title]
        title = m["title"].format(**fmt)
        text = m["message"].format(**fmt)
        return title, text
    title = key_or_title.format(**fmt)
    text = (message or "").format(**fmt)
    return title, text
    
def confirm(key_or_title: str, parent: Misc | None=None, message: str | None=None, **fmt) -> None:
    title, text = resolve(key_or_title, message, **fmt)
    return messagebox.askyesno(title, text, parent=parent)

def info(key_or_title: str, parent: Misc | None=None, message: str | None=None, **fmt) -> None: 
    title, text = resolve(key_or_title, message, **fmt)
    messagebox.showinfo(title, text, parent=parent)

def error(key_or_title: str, parent: Misc | None=None, message: str | None=None, **fmt) -> None: 
    title, text = resolve(key_or_title, message, **fmt)
    messagebox.showerror(title, text, parent=parent)