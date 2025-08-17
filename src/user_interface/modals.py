from __future__ import annotations
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict

from src.config import ICON_ICO, ICON_PNG
from .player_dialogs import resolve, confirm, info, error

#
# Helper Functions
#
def _apply_window_icons(win: tk.Toplevel)-> None:
    ico = Path(ICON_ICO)
    png = Path(ICON_PNG)
    if sys.platform.startswith("win") and ico.is_file():
        try:
            win.iconbitmap(str(ico))
        except tk.TclError:
            pass
    if png.is_file():
        try:
            win._icon_ref = tk.PhotoImage(file=str(png))
            win.iconphoto(True, win._icon_ref)
        except tk.TclError:
            pass    

def _center_on_parent(win: tk.Toplevel, parent: tk.Misc, margin: int  = 16) -> None: 
    win.update_idletasks()

    parent = parent.winfo_toplevel()
    parent_x, parent_y = parent.winfo_rootx(), parent.winfo_rooty()
    parent_width, parent_height = parent.winfo_width(), parent.winfo_height()

    ww, wh = win.winfo_reqwidth(), win.winfo_reqheight()

    x = parent_x + (parent_width - ww) // 2
    y = parent_y + (parent_height - wh) // 2

    screen_x, screen_y = win.winfo_screenwidth(), win.winfo_screenheight()
    x = max(margin, min(x, screen_x - ww - margin))
    y = max(margin, min(y, screen_y - wh - margin))

    win.geometry(f"+{x}+{y}")

#
#Dialogs and Modals
#

def add_player_dialog(
        parent: tk.Misc,
        team_names: Dict[str, tk.StringVar], 
        default_team: str = "home", 
        positions: list[str] | None = None,
) -> Optional[Dict]:

    positions = positions or ["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"]

    win=tk.Toplevel(parent)
    win.withdraw()
    win.title("Add Player")
    win.transient(parent)
    win.resizable(False, False)
    win.grab_set()

    frm = ttk.Frame(win, padding=12)
    frm.grid(sticky="nsew")
    win.grid_columnconfigure(0, weight = 1)

    ttk.Label(frm, text="Name").grid(row=0, column=0, sticky="w")
    name_var = tk.StringVar()
    name_ent = ttk.Entry(frm, textvariable=name_var, width = 28)
    name_ent.grid(row = 1, column = 0, sticky = "ew", pady = (2, 10))

    ttk.Label(frm, text="Position").grid(row=2, column=0, sticky="w")
    pos_var = tk.StringVar(value=positions[0])
    pos_cb = ttk.Combobox(frm, textvariable=pos_var, values = positions, state = "readonly")
    pos_cb.grid(row = 3, column = 0, sticky= "ew", pady = (2, 10))
                                         
    ttk.Label(frm, text="Team").grid(row=4, column=0, sticky="w")
    team_keys = list(team_names.keys())
    team_labels = [team_names[k].get() for k in team_keys]
    label_to_key = {lbl: k for lbl, k in zip(team_labels, team_keys)}

    default_label = team_names.get(default_team, tk.StringVar(value="")).get()
    team_var = tk.StringVar(value = default_label if default_label in team_labels else team_labels[0])

    team_cb = ttk.Combobox(frm, textvariable=team_var, values = team_labels, state="readonly")
    team_cb.grid(row = 5, column = 0, sticky = "ew", pady = (2,10))
                                         
    btns = ttk.Frame(frm)
    btns.grid(row = 6, column = 0, sticky = "e")

    result = list[Optional[dict]] = [None]

    def on_ok():
        name = name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing Name", "Enter a Player Name", parent = win)
            name_ent.focus_set()
            return
        pos = pos_var.get()
        team_label = team_var.get()
        team_key = label_to_key(team_label, default_team)
        result[0]={"name": name, "position": pos, "team_key": team_key}
        win.destroy()

    def on_cancel() -> None:
        result[0] = None 
        win.destroy()

    ttk.Button(btns, text="Cancel", command=on_cancel).grid(row=0, column=0, padx=(0,6))
    ttk.Button(btns, text="Add", command=on_ok).grid(row=0, column=1)

    win.bind("<Return>", lambda _: on_ok())
    win.bind("<Escape>", lambda _: on_cancel())
    
    name_ent.focus_set()
    _center_on_parent(win, parent)
    win.deiconify()

    parent.wait_window(win)
    return result [0]

def _center_on_parent(win: tk.Toplevel, parent: tk.Misc) -> None: 
    win.update_idletasks()
    try: 
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        ww, wh = win.winfo_width(), win.winfo_height()
        x = px + (pw - ww) // 2
        y = py + (ph - wh) // 2
    except Exception:
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        ww, wh = win.winfo_width(), win.winfo_height()
        x = (sw - ww) // 2
        y = (sh - wh) // 2
        
    win.geometry(f"+{x}+{y}")                        


def rename_team_dialog(parent: tk.Misc, current_name:str) -> Optional[str]:
    win = tk.Toplevel(parent)
    win.title("Rename Team")
    win.transient(parent)
    win.resizable(False, False)

    win.grab_set()
    parent.update_idletasks()

    frm = ttk.Frame(win, padding=12)
    frm.grid(sticky="nsew")
    frm.grid_columnconfigure(0, weight=1)
    frm.grid_rowconfigure(0, weight=1)

    name_var = tk.StringVar(value=current_name)
                            
    ttk.Label(frm, text="Team Name").grid(row=0, column=0, padx=(0,6), sticky="w")
    entry = ttk.Entry(frm, textvariable=name_var, width=28)
    entry.grid(row=1, column=0, padx=0, pady=(0,12), sticky="ew")
    entry.select_range(0, tk.END)

    btns = ttk.Frame(win)
    btns.grid(row=2, column=0, pady=(0,0), sticky="e")
    
    result = [None]
    
    def on_ok():
       val = name_var.get().strip()
       if not val: 
           messagebox.showwarning("Missing Name", "Please enter a team name", parent=win)
           return
       result[0] = val if val != current_name else None
       win.destroy()

    def on_cancel():
        result[0] = None
        win.destroy()

    ttk.Button(btns, text="Cancel", command=on_cancel).grid(row=0, column=0, padx=(0,6))
    ttk.Button(btns, text="OK", command=on_ok).grid(row=0, column=1)

    win.bind("<Return>", lambda _: on_ok())
    win.bind("<Escape>", lambda _: on_cancel()) 
    win.protocol("WM_DELETE_WINDOW", on_cancel)

    entry.focus_set()
    win.update_idletasks()
    try: 
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        ww, wh = win.winfo_width(), win.winfo_height()
        win.geometry(f"+{px + (pw-ww)//2}+{py + (ph-wh)//2}")
    except Exception: 
        pass 

    win.wait_window()
    return result[0]

