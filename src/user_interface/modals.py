from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from .player_dialogs import resolve, confirm, info, error

def add_player_dialog(parent: tk.Misc, team: str, positions: list[str]) -> Optional[dict]:
    win=tk.Toplevel(parent)
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
    x=parent.winfo_rootx() + (parent.winfo_width() - win.winfo_width())//2
    y=parent.winfo_rooty() + (parent.winfo_height() - win.winfo_height())//2
    win.geometry(f"+{x}+{y}")

    parent.wait_window(win)
    return result                               


def rename_team_dialog(parent: tk.Misc, current_name:str) -> str | None:
    master = parent.winfo_toplevel()
    
    win = tk.Toplevel(parent)
    win.title("Rename Team")
    win.transient(parent)
    win.resizable(False, False)

    win.grab_set()

    name_var = tk.StringVar(value=current_name)

    '''
    frm=ttk.Frame(win, padding=12)
    frm.grid(sticky="nsew")
    frm.grid_columnconfigure(1, weight=1)
    '''

    ttk.Label(win, text="Team Name").grid(row=0, column=0, padx=12, pady=(12,6), sticky="w")
    name_var = tk.StringVar(value=current_name)
    entry = ttk.Entry(win, textvariable=name_var, width=28)
    entry.grid(row = 1, column= 0, padx = 12, pady=(0,12), sticky="ew")
    entry.focus_set()
    win.columnconfigure(0, weight=1)

    result: list[str | None] = [None]
    
    def on_ok():
       val = name_var.get().strip()
       result[0] = val if val != current_name else None
       win.destroy()

    def on_cancel():
        result[0] = None
        win.destroy()

    btns = ttk.Frame(win)
    btns.grid(row=2, column=0, padx=12, pady=(0,12), sticky="e")
    ttk.Button(btns, text="Cancel", command=on_cancel).grid(row=0, column=0, padx=(0,6))
    ttk.Button(btns, text="OK", command=on_ok).grid(row=0, column=1)

    win.bind("<Return>", lambda _: on_ok())
    win.bind("<Escape>", lambda _: on_cancel()) 

    win.update_idletasks()
    px = parent.winfo_rootx() + (parent.winfo_width() - win.winfo_width()) // 2
    py = parent.winfo_rooty() + (parent.winfo_height() - win.winfo_height()) // 2
    win.geometry(f"+{px}+{py}")

    parent.wait_window(win)
    return result[0]
                                                        
