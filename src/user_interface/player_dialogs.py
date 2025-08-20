from __future__ import annotations
from tkinter import messagebox, Toplevel, ttk, StringVar, Misc, Entry, Frame

MESSAGES: dict[str, dict[str, str]] = {
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
        "message": "Reset the Court?"
    },
    "confirm_end": {
        "title": "End Game?",
        "message": "End the Game?"
    },
    "confirm_remove_player": {
        "title": "Remove Player?",
        "message": "Remove {name} from {team}?"
    },
    "export_success": { 
        "title": "Export Complete", 
        "message": "Saved: {path}"    
    }, 
    "export_fail": {
        "title": "Export Failed", 
        "message": 
            "Sorry, I couldn't save the image to {path}"
        }
    }
#Will add more as they appear
#Will add "load" section for load-related messages
#Will add "save" section for save-related messages 

def resolve(key_or_title: str, message: str | None = None, **fmt) -> tuple[str, str]:
    key = str(key_or_title).strip().lower()
    ALIAS = {
        "confirm_quit": "quit", 
        "exit": "quit",
        "export success": "export_success",
        "export fail": "export_fail"
    }
    key = ALIAS.get(key, key)

    if key in MESSAGES:
        m = MESSAGES[key]
        try:
            title = m["title"].format(**fmt)
            text = m["message"].format(**fmt)
        except Exception: 
            title = m["title"]
            text = m["message"]
    else: 
        try: 
            title = key_or_title.format(**fmt)
            text = (message or "").format(**fmt)
        except Exception: 
            title = str(key_or_title)
            text = (message or "")
    return title, text 
    
def confirm(key_or_title: str, parent: Misc | None=None, message: str | None=None, **fmt) -> bool:
    title, text = resolve(key_or_title, message, **fmt)
    master = None if parent is None else parent.winfo_toplevel()
    return messagebox.askyesno(title, text, parent=master)

def info(key_or_title: str, parent: Misc | None=None, message: str | None=None, **fmt) -> None: 
    title, text = resolve(key_or_title, message, **fmt)
    master = None if parent is None else parent.winfo_toplevel()
    messagebox.showinfo(title, text, parent=master)

def error(key_or_title: str, parent: Misc | None=None, message: str | None=None, **fmt) -> None: 
    title, text = resolve(key_or_title, message, **fmt)
    master = None if parent is None else parent.winfo_toplevel()
    messagebox.showerror(title, text, parent=master)
