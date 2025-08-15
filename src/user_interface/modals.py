from __future__ import annotations
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

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

def add_player_dialog(parent: tk.Misc, team: str, positions: list[str]) -> Optional[dict]:
    win=tk.Toplevel(parent)
    win.withdraw()
    win.title("Add Player")
    win.transient(parent)
    win.grab_set()

    name_var = tk.StringVar()
    pos_var = tk.StringVar(value=positions[0] if positions else "")
    team_var =tk.StringVar(value=team)

    frm = ttk.Frame(win, padding=12)
    frm.grid(sticky="nsew")
    for index in range(2):
        frm.grid_columnconfigure(index, weight=1)

    ttk.Label(frm, text="Name").grid(row=0, column=0, sticky="w", padx=4, pady=4)
    ttk.Entry(frm, textvariable=name_var).grid(row=0, column=1, sticky="ew", padx=4, pady=4)

    ttk.Label(frm, text="Position").grid(row=1, column=0, sticky="w", padx=4, pady=4)
    ttk.OptionMenu(frm, pos_var, pos_var.get(), *positions).grid(row=1, columns=1, sticky="ew", padx=4, pady=4)

    ttk.Label(frm, text="Team").grid(row=2, column=0, sticky="w",padx=4, pady=4)
    ttk.Entry(frm, textvariable=team_var, state="readonly").grid(row=2, column=1, sticky="ew", padx=4, pady=4)

    result: Optional[dict] = None

    def on_ok():
        nonlocal result 
        name = name_var.get().strip()
        if not name: 
            messagebox.showwarning("Missing Name", "Enter a Player Name.", parent=win)
            return
        result={"name": name, "position": pos_var.get(), "team": team_var.get()}
        win.destroy

    def on_cancel():
        win.destroy()

    btns = ttk.Frame(frm)
    btns.grid(row=3, column=0, columnspan=2, pady=(10,0))
    ttk.Button(btns, text="Cancel", command=on_cancel).grid(row=0, column=0, padx=6)
    ttk.Button(btns, text="Add", command=on_ok).grid(row=0, column=1, padx=6)

    win.bind("<Return>", lambda _: on_ok())
    win.bind("<Escape>", lambda _: on_cancel())

    win.update_idletasks()
    _center_on_parent(win, parent)
    win.deiconify()

    parent.wait_window(win)
    return result                               


def rename_team_dialog(parent: tk.Misc, current_name:str) -> str | None:
    win = tk.Toplevel(parent)
    win.withdraw()
    win.title("Rename Team")
    win.resizable(False, False)
    _apply_window_icons(win)

    frm = ttk.Frame(win, padding=12)
    frm.grid(sticky="nsew")
    frm.grid_columnconfigure(0, weight=1)

    name_var = tk.StringVar(value=current_name)
                            
    ttk.Label(frm, text="Team Name").grid(row=0, column=0, padx=(0,6), sticky="w")
    entry = ttk.Entry(frm, textvariable=name_var, width=28)
    entry.grid(row=1, column=0, padx=0, pady=(0,12), sticky="ew")
    entry.focus_set()

    btns = ttk.Frame(win)
    btns.grid(row=2, column=0, pady=(0,0), sticky="e")
    
    result: list[str | None] = None
    
    def on_ok():
       val = name_var.get().strip()
       result[0] = val if val != current_name else None
       win.destroy()

    def on_cancel():
        result[0] = None
        win.destroy()

    ttk.Button(btns, text="Cancel", command=on_cancel).grid(row=0, column=0, padx=(0,6))
    ttk.Button(btns, text="OK", command=on_ok).grid(row=0, column=1)

    win.bind("<Return>", lambda _: on_ok())
    win.bind("<Escape>", lambda _: on_cancel()) 

    win.update_idletasks()
    _center_on_parent(win, parent)
    win.deiconify()
    win.grab_set()
    win.focus_set()

    parent.wait_window(win)
    return result[0]
                                                        

