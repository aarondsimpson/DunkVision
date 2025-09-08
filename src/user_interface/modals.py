from __future__ import annotations
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional, Dict
from datetime import date
import calendar as _calendar

from src.config import ICON_ICO, ICON_PNG
from src.user_interface.player_dialogs import resolve, confirm, info, error

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

    _apply_window_icons(win)

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

    result: list[Optional[dict]] = [None]

    def on_ok():
        name = name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing Name", "Enter a Player Name", parent = win)
            name_ent.focus_set()
            return
        pos = pos_var.get()
        team_label = team_var.get()
        team_key = label_to_key.get(team_label, default_team)
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


def rename_team_dialog(parent: tk.Misc, current_name:str) -> Optional[str]:
    win = tk.Toplevel(parent)
    win.title("Rename Team")
    win.transient(parent)
    win.resizable(False, False)

    win.grab_set()
    parent.update_idletasks()

    try: 
        _apply_window_icons(win)
    except Exception: 
        pass

    frm = ttk.Frame(win, padding=12)
    frm.grid(sticky="nsew")
    frm.grid_columnconfigure(0, weight=1)
    frm.grid_rowconfigure(0, weight=1)

    name_var = tk.StringVar(value=current_name)
    save_var = tk.BooleanVar(value=False)
                            
    ttk.Label(frm, text="Team Name").grid(row=0, column=0, padx=(0,6), sticky="w")
    entry = ttk.Entry(frm, textvariable=name_var, width=28)
    entry.grid(row=1, column=0, padx=0, pady=(0,12), sticky="ew")
    entry.select_range(0, tk.END)

    save_cb = ttk.Checkbutton(frm, text="Save Team Roster", variable=save_var)
    save_cb.grid(row=2, column=0, sticky="w", pady=(0,8))

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
    
    try: 
        win.protocol("WM_DELETE_WINDOW", on_cancel)
    except Exception: 
        pass

    entry.focus_set()
    try: 
        _center_on_parent(win, parent)
    except Exception: 
        pass
    win.deiconify()
    parent.wait_window(win)
    return result[0]


def shot_result_dialog(parent, *, show_and1: bool = True) -> dict | None:
    win = tk.Toplevel(parent)
    win.title("Shot Result")
    win.transient(parent)
    win.resizable(False, False)
    win.grab_set()
    _apply_window_icons(win)

    frm = ttk.Frame(win, padding = 12)
    frm.grid(sticky = "nsew")
    ttk.Label(frm, text = "Shot Result?").grid(row = 0, column = 0, columnspan = 2, pady = (0,10))

    result = {"made": None, "and1": False}

    def _set(val: bool):
        result["made"] = val
        win.destroy()

    ttk.Button(frm, text = "Made", command = lambda: _set(True)).grid(row = 1, column = 0, padx = (0,6))
    ttk.Button(frm, text = "Missed", command = lambda: _set(False)).grid(row = 1, column = 1, padx = (6,0))

    if show_and1:
        and1_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="And-1", variable=and1_var).grid(
            row=2, column=0, columnspan=2, pady=(10,0))
        def _sync_and1(*_):
            result["and1"] = bool(and1_var.get())
        and1_var.trace_add("write", _sync_and1)
        _sync_and1()

    win.bind("<Escape>", lambda _e: _set(None))
    win.update_idletasks()
    _center_on_parent(win, parent)
    parent.wait_window(win)

    if result["made"] is None:
        return None
    return result  

def choose_one_dialog(parent, *, title: str, prompt: str, options: list[str]) -> str | None:  # <-- new
    """Returns the chosen label or None."""
    win = tk.Toplevel(parent)
    win.title(title)
    win.transient(parent)
    win.resizable(False, False)
    win.grab_set()
    _apply_window_icons(win)

    frm = ttk.Frame(win, padding=12)
    frm.grid(sticky="nsew")

    ttk.Label(frm, text=prompt).grid(row=0, column=0, columnspan=len(options), pady=(0,8))

    chosen = {"val": None}
    def _set(v): chosen["val"] = v; win.destroy()

    for i, lab in enumerate(options):
        ttk.Button(frm, text=lab, command=lambda v=lab: _set(v)).grid(row=1, column=i, padx=4)

    win.bind("<Escape>", lambda _e: _set(None))
    win.update_idletasks()
    _center_on_parent(win, parent)
    parent.wait_window(win)
    return chosen["val"]

def free_throw_reason_dialog(parent) -> str | None:
    return choose_one_dialog(
        parent, title="Free Throw Source",
        prompt="Why was the free throw awarded?",
        options=["And-1", "Technical", "Flagrant"],
    )

def game_metadata_dialog(parent) -> dict | None: 
    try: 
        from tkcalendar import DateEntry
        _HAS_TKCALENDAR = True
    except Exception: 
        _HAS_TKCALENDAR = False 

    win = tk.Toplevel(parent)
    win.withdraw()
    win.title("Game Details")
    win.transient(parent)
    win.resizable(False, False)
    win.grab_set()

    _apply_window_icons(win)

    frm = ttk.Frame(win, padding=12)
    frm.grid(sticky="nsew")
    win.grid_columnconfigure(0, weight=1)

    ttk.Label(frm, text="Date").grid(row=0, column=0, sticky="w")

    if _HAS_TKCALENDAR:
        date_var = tk.StringVar()
        date_ctl = DateEntry(frm, textvariable=date_var, date_pattern="yyyy-mm-dd")
        # initialize with today's date
        date_ctl.set_date(date.today())
        date_var.set(date.today().isoformat())
        date_ctl.grid(row=1, column=0, sticky="ew", pady=(2, 10))
    else:
        # Fallback: 3 pickers (Month / Day / Year)
        today = date.today()
        y_var = tk.IntVar(value=today.year)
        m_var = tk.IntVar(value=today.month)
        d_var = tk.IntVar(value=today.day)

        row = ttk.Frame(frm)
        row.grid(row=1, column=0, sticky="ew", pady=(2, 10))
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=1)
        row.grid_columnconfigure(2, weight=1)

        years = list(range(today.year - 5, today.year + 6))
        months = list(range(1, 13))

        y_cb = ttk.Combobox(row, values=years, state="readonly", textvariable=y_var, width=6)
        m_cb = ttk.Combobox(row, values=months, state="readonly", textvariable=m_var, width=4)
        d_cb = ttk.Combobox(row, state="readonly", width=4, values=[])

        def _sync_days(*_):
            y = y_var.get()
            m = m_var.get()
            nd = _calendar.monthrange(y, m)[1]
            days = list(range(1, nd + 1))
            cur = min(d_var.get(), nd)
            d_cb.configure(values=days)
            d_var.set(cur)

        m_cb.bind("<<ComboboxSelected>>", _sync_days)
        y_cb.bind("<<ComboboxSelected>>", _sync_days)

        y_cb.grid(row=0, column=0, padx=(0, 6))
        m_cb.grid(row=0, column=1, padx=(0, 6))
        d_cb.grid(row=0, column=2, padx=(0, 0))

        d_cb.configure(textvariable=d_var)
        _sync_days()

        def _get_iso():
            return date(y_var.get(), m_var.get(), d_var.get()).isoformat()

    ttk.Label(frm, text="Location").grid(row=2, column=0, sticky="w")
    loc_var = tk.StringVar(value="")
    loc_ent = ttk.Entry(frm, textvariable=loc_var, width=28)
    loc_ent.grid(row=3, column=0, sticky="ew", pady=(2, 10))

    btns = ttk.Frame(frm)
    btns.grid(row=4, column=0, sticky="e")

    result = [None]

    def on_ok():
        if _HAS_TKCALENDAR:
            iso = date_ctl.get_date().isoformat()
        else:
            try:
                iso = _get_iso()
            except Exception:
                messagebox.showwarning("Invalid Date", "Please select a valid date.", parent=win)
                return

        loc = loc_var.get().strip()
        if not loc:
            messagebox.showwarning("Missing Location", "Please enter a location.", parent=win)
            loc_ent.focus_set()
            return
        result[0] = {"date": iso, "location": loc}
        win.destroy()

    def on_cancel():
        result[0] = {
            "date": date.today().isoformat(),
            "location": "Unknown",
        }
        win.destroy()

    ttk.Button(btns, text="Cancel", command=on_cancel).grid(row=0, column=0, padx=(0, 6))
    ttk.Button(btns, text="OK", command=on_ok).grid(row=0, column=1)

    win.bind("<Return>", lambda _: on_ok())
    win.bind("<Escape>", lambda _: on_cancel())
    win.protocol("WM_DELETE_WINDOW", on_cancel)

    # focus and center
    loc_ent.focus_set()
    _center_on_parent(win, parent)
    win.deiconify()
    parent.wait_window(win)
    return result[0]

def dunk_or_layup_dialog(parent) -> str | None:  
    win = tk.Toplevel(parent)                    
    win.title("Shot Type")                       
    win.transient(parent)                        
    win.resizable(False, False)                  
    win.grab_set()
    _apply_window_icons(win)                               

    frm = ttk.Frame(win, padding=12)             
    frm.grid(sticky="nsew")                      
    ttk.Label(frm, text="Dunk or Layup?").grid(  
        row=0, column=0, columnspan=2, pady=(0, 10)  
    )                                            

    result = {"val": None}                       

    def _set(v: str):                            
        result["val"] = v                        
        win.destroy()                            

    ttk.Button(frm, text="Dunk",                
               command=lambda: _set("Dunk")     
               ).grid(row=1, column=0, padx=(0, 6))  
    ttk.Button(frm, text="Layup",               
               command=lambda: _set("Layup")    
               ).grid(row=1, column=1, padx=(6, 0))  

    win.bind("<Escape>", lambda _e: _set(None))  
    win.update_idletasks()                       

    try:                                         
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        ww, wh = win.winfo_width(), win.winfo_height()
        win.geometry(f"+{px + (pw-ww)//2}+{py + (ph-wh)//2}")
    except Exception:
        pass

    parent.wait_window(win)                      
    return result["val"]                         

def manage_teams_modal(parent, *, team_names: list[str]) -> dict | None:
    win = tk.Toplevel(parent)
    win.title("Manage Teams")
    win.transient(parent)
    win.resizable(False, False)
    win.grab_set()
    _apply_window_icons(win)

    frm = ttk.Frame(win, padding=12)
    frm.grid(sticky="nsew")

    ttk.Label(frm, text="Saved Teams").grid(row=0, column=0, sticky="w")
    names = team_names[:] or []
    sel = tk.StringVar(value=names[0] if names else "")

    dd = ttk.OptionMenu(frm, sel, sel.get(), *names)  # empty is ok
    dd.grid(row=1, column=0, sticky="ew", pady=(2, 10))
    frm.grid_columnconfigure(0, weight=1)

    btn_row1 = ttk.Frame(frm); btn_row1.grid(row=2, column=0, sticky="ew", pady=(0, 8))
    btn_row2 = ttk.Frame(frm); btn_row2.grid(row=3, column=0, sticky="ew")

    result = {"val": None}

    def _need_sel() -> str | None:
        name = sel.get().strip()
        if not name:
            messagebox.showinfo("Manage Teams", "No saved teams yet.", parent=win)
            return None
        return name

    def _set(val): result["val"] = val; win.destroy()

    ttk.Button(btn_row1, text="Apply to Home",
               command=lambda: (_set({"action":"apply_home","name":_need_sel()})
                                if _need_sel() else None)
               ).pack(side="left", padx=(0,6))

    ttk.Button(btn_row1, text="Apply to Away",
               command=lambda: (_set({"action":"apply_away","name":_need_sel()})
                                if _need_sel() else None)
               ).pack(side="left")

    ttk.Button(btn_row2, text="Rename",
               command=lambda: (
                   lambda _n=_need_sel():
                       _set({"action":"rename","name":_n,"new_name":
                            simpledialog.askstring("Rename Team", f"Rename '{_n}' to:", parent=win) or ""})
                   )() if _need_sel() else None
               ).pack(side="left", padx=(0,6))

    ttk.Button(btn_row2, text="Delete",
               command=lambda: (_set({"action":"delete","name":_need_sel()})
                                if _need_sel() else None)
               ).pack(side="left")

    ttk.Button(frm, text="Close", command=lambda: _set(None)).grid(row=4, column=0, sticky="e", pady=(10,0))

    _center_on_parent(win, parent)
    win.deiconify()
    parent.wait_window(win)
    return result["val"]
