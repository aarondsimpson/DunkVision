import tkinter as tk
from tkinter import ttk

from src.user_interface.player_dialogs import resolve, confirm, info, error, MESSAGES

def add_player_dialog(parent: Misc, team: str, positions: list[str]) -> dict | None: 
    win=Toplevel(parent)
    win.title("Add Player")
    win.transient(parent)
    win.grab_set()

    name_var = StringVar()
    pos_var = StringVar(value=positions[0] if positions else "")
    team_var =StringVar(value=team)

    frm = ttk.Frame(win, padding=12)
    frm.grid(sticky="nsew")
    for index in range(2):
        frm.grid_columnconfigure(index, weight=1)

    ttk.Label(frm, text="Name").grid(row=0, column=0, sticky="w", padx=4, pady=4)
    Entry(frm, textvariable=name_var).grid(row=0, column=1, sticky="ew", padx=4, pady=4)

    ttk.Label(frm, text="Position").grid(row=1, column=0, sticky="w", padx=4, pady=4)
    ttk.OptionMenu(frm, pos_var, pos_var.get(), *positions).grid(row=1, columns=1, sticky="ew", padx=4, pady=4)

    ttk.Label(frm, text="Team").grid(row=2, column=0, sticky="w",padx=4, pady=4)
    Entry(frm, textvariable=team_var, state="readonly").grid(row=2, column=1, sticky="ew", padx=4, pady=4)

    result: dict | None = None

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
    