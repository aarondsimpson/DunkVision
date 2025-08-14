import json 
import csv
import tkinter as tk

from tkinter import ttk, filedialog
from PIL import ImageGrab

from .court_canvas import ScreenImage
from .player_dialogs import confirm, info, error
from .modals import add_player_dialog as add_player_modal, rename_team_dialog

BAR_HEIGHT = 60
SIDE_WIDTH = 220

MODE = {
    "light": {
        "image": "court_light", 
        "bg": "#BCA382",
        "list": "#BCA382"},
    "dark": {
        "image": "court_dark", 
        "bg": "#7C90C5",
        "list": "#7C90C5"}
    }

class CourtFrame(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller=self
        
        #State Definition 
        self.mode="dark"
        self.quarter=tk.StringVar(value="Q1")
        self.actions=[]
        self.redo_stack=[]
        self.data_points=[]
        self.team_order=["home","away"]
        
        self.team_names={
            "home": tk.StringVar(value="My Team"),
            "away": tk.StringVar(value="Their Team")
        }
        self.rosters={
            "home": ["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"],
            "away": ["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"],
        }
        self.selected_team_key=tk.StringVar(value="home")

        #Layout Scaffold
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        #Widget Scaffold
        self.topbar=TopBar(
            self, 
            on_toggle_mode=self.toggle_mode,
            on_home_button=self.home_button,
            on_undo_action=self.undo_action,
            on_redo_action=self.redo_action,
            on_select_quarter=self.select_quarter,
            on_save_game=self.save_game,
            on_reset_game=self.reset_game,
            on_end_game=self.end_game, 
            on_export_image=self.export_image,
            on_export_csv=self.export_csv,
            on_export_json=self.export_json,
            quarter_var=self.quarter, 
            )
        self.topbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0,4))

        self.sidebar=SideBar(self, controller=self)
        self.sidebar.grid(row=1, column=0, sticky="ns")

        self.center_canvas=ScreenImage(self)
        self.center_canvas.grid(row=1, column=1, sticky="nsew")

        self.after_idle(self.update_mode)
        
        self.databar = DataBar(self, controller=self)
        self.databar.grid(row=1, column=2, sticky="ns")

        self.statusbar=StatusBar(self)
        self.statusbar.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(4,0))

        self.refresh_stats()   

    def toggle_mode(self):
        self.mode="dark" if self.mode == "light" else "light"
        self.update_mode()
        self.set_status(f"Theme: {self.mode.title()}")
        
    def update_mode(self):
        cfg = MODE[self.mode]
        self.center_canvas.show(cfg["image"])

        style = ttk.Style(self)
        style.configure("TopBar.TFrame", background = cfg["bg"])
        style.configure("SideBar.TFrame", background = cfg["bg"])
        style.configure("StatusBar.TFrame", background = cfg["bg"])
        style.configure("PlayerList.TFrame", background = cfg["list"])
        style.configure("DataBar.TFrame", background = cfg["bg"])

        self.topbar.configure(style="TopBar.TFrame")
        self.sidebar.configure(style="SideBar.TFrame")
        self.statusbar.configure(style="StatusBar.TFrame")
        self.databar.configure(style="DataBar.TFrame")

        if self.mode == "dark":
            self.sidebar.set_card_colors(fill="#E8EDF6", border="#A8B3C5")
        else: 
            self.sidebar.set_card_colors(fill="#EFE9DD", border="#BDAA90")

    def home_button(self):
        if confirm("confirm_home",parent=self):
            if hasattr(self.controller, "go_home") and callable(self.controller.go_home):
                self.controller.go_home()
            else:
                info("Not Wired", self, "Home navigation is not wired yet.")
        
    def undo_action(self):
        if not self.actions:
            self.set_status("Nothing to Undo.")
            return
        action=self.actions.pop()
        self.redo_stack.append(action)
        self.set_status(f"Undid: {action.get('type', 'action')}") #Requires build out when canvas drawing is coded

    def redo_action(self):
        if not self.redo_stack:
            self.set_status("Nothing to Redo.")
            return 
        action=self.redo_stack.pop()
        self.actions.append(action)
        self.set_status(f"Redid: {action.get('type', 'action')}") #Requires build out when canvas drawing is coded 

    def select_quarter(self, q:str):
        self.quarter.set(q)
        self.set_status(f"Quarter: {q}")
                
    def save_game(self):
        self.set_status("Save game (stub).") #Requires build out when saving persistence format is built

    def reset_game(self):
        if not confirm("confirm_reset", self):
            return    
        self.actions.clear()
        self.redo_stack.clear()
        self.data_points.clear()
        self.center_canvas.show(MODE[self.mode]["image"])
        self.refresh_stats()
        self.set_status("Reset.")
                   
    def end_game(self):
        self.set_status("End game (stub).") #Build confirmation dialog

    def export_image(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")],
            title="Export Court Image",
        )
        if not path: 
            return
        c=self.center_canvas.canvas
        x=c.winfo_rootx()
        y=c.winfo_rooty()
        w=x+c.winfo_width()
        h=y+c.winfo_height()
        img = ImageGrab.grab(bbox=(x, y, w, h))
        img.save(path)
        self.set_status(f"Image Exported: {path}")
    
    def export_json(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            title="Export Data (JSON)",
        )
        if not path:
            return 
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data_points, f, ensure_ascii=False, indent=2)
        self.set_status(f"JSON Exported: {path}")

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Export Data (CSV)",
        )
        if not path:
            return
        rows = self.data_points
        if not rows: 
            with open(path, "w", newline="", encoding="utf-8") as f:
                f.write("")
            self.set_status(f"CSV Exported (Empty): {path}")
            return
        fieldnames = sorted({k for row in rows for k in row.keys()})
        with open(path, "w", newline="",encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        self.set_status(f"CSV Exported: {path}")

    def set_status(self, text: str):
        if hasattr(self.statusbar, "set_status"):
            self.statusbar.set_status(text)

    def rename_team(self, team_key: str):
        if team_key not in self.team_names:
            self.set_status(f"Unknown Team Key: {team_key}")
            return
        current = self.team_names[team_key].get()
        new_name = rename_team_dialog(self, current)
        if not new_name or new_name == current: 
            return
        self.team_names[team_key].set(new_name)
        if hasattr(self.sidebar, "refresh_team_dropdown"):
            self.sidebar.refresh_team_dropdown()
        self.set_status(f"Team Renamed: {current} -> {new_name}")

    def refresh_stats(self):
        if hasattr(self, "databar") and hasattr(self.databar, "refresh_from_points"):
            self.databar.refresh_from_points(self.data_points)

    def record_shot(self, *, team: str, x: int, y: int, made: bool, airball: bool=False, meta: dict|None=None):
        point = {
            "team": team, 
            "x": int(x), "y": int(y),
            "made": bool(made), "airball": bool(airball),
            "quarter": self.quarter.get(),
        }
        if meta: point.update(meta)

        self.data_points.append(point)
        self.actions.append({"type": "shot", "data": point})
        self.redo_stack.clear()
        self.refresh_stats()

        team_name = self.team_names[team].get()
        outcome = "Made" if made else ("Airball" if airball else "Missed")
        self.set_status(f"Recorded Shot: {team_name} - {outcome} (Q{self.quarter.get()[-1]}, x:{x}, y:{y})")
             

class TopBar(ttk.Frame):
    def __init__(
            self, parent, 
            on_toggle_mode=None, on_home_button=None,
            on_undo_action=None, on_redo_action=None, 
            on_select_quarter=None, on_end_game=None,
            on_save_game=None, on_reset_game=None,  
            on_export_image=None, on_export_json=None, on_export_csv=None,
            quarter_var: tk.StringVar | None=None,
    ):              
        super().__init__(parent, padding=(8, 10))
        self.grid_propagate(False)
        self.configure(height = BAR_HEIGHT)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        left=ttk.Frame(self)
        left.grid(row=0,column=0, sticky="w", padx=8)

        #ttk.Label(left, text="Dunk Vision").grid(row=0, column=0, padx=(0,8))#Consider removing this - If so, update column numbers below so they shift left. 
        ttk.Button(left, text="Home", command=on_home_button or (lambda:None)).grid(row=0, column=1, padx=3)
        ttk.Button(left, text="Theme", command=on_toggle_mode or (lambda:None)).grid(row=0, column=2, padx=3)

        mid=ttk.Frame(self)
        mid.grid(row=0, column=1)

        ttk.Button(mid, text="Undo", command=on_undo_action or (lambda:None)).grid(row=0, column=0, padx=3)
        ttk.Button(mid, text="Redo", command=on_redo_action or (lambda:None)).grid(row=0, column=1, padx=3)

        qvar=quarter_var or tk.StringVar(value="Q1")
        for index, quarter in enumerate(("Q1", "Q2", "Q3", "Q4"), start=0):
            ttk.Radiobutton(
                mid, text=quarter, value=quarter, variable=qvar,
                command=(lambda qq=quarter: (on_select_quarter or (lambda _q: None))(qq))
            ).grid(row=0, column=2+index, padx=3)
        
        right=ttk.Frame(self)
        right.grid(row=0, column=2, sticky="e", padx=8)

        ttk.Button(right, text="Save", command=on_save_game or (lambda:None)).grid(row=0, column=0, padx=3)
        ttk.Button(right, text="Reset", command=on_reset_game or (lambda:None)).grid(row=0, column=1, padx=3)
        ttk.Button(right, text="End Game", command=on_end_game or (lambda:None)).grid(row=0, column=2, padx=3)

        ttk.Button(right, text="Export Image", command=on_export_image or (lambda:None)).grid(row=0, column=3, padx=(12,3))
        ttk.Button(right, text="Export JSON", command=on_export_json or (lambda:None)).grid(row=0, column=4, padx=3)
        ttk.Button(right, text="Export CSV", command=on_export_csv or (lambda:None)).grid(row=0, column=5, padx=3)

       

class SideBar(ttk.Frame):
    def __init__(self, parent, controller = None): 
        super().__init__(parent)
        self.controller = controller
        print("DEBUG: controller type in SideBar:", type(controller), flush=True)
        self.grid_propagate(False)
        self.configure(width = SIDE_WIDTH)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.card = tk.Frame(
            self, 
            bg = "#E8EDF6",
            highlightthickness=1,
            highlightbackground= "#A8B3C5",
        )
        self.card.grid(row=0, column=0, sticky="nsew", padx=8, pady=10)
        self.inner = ttk.Frame(self.card, padding=8)
        self.inner.pack(fill="both", expand=True)

        style=ttk.Style(self)
        style.configure("Player.TButton", padding=4)
        style.configure("PlayerSelected.TButton", padding=4, relief="sunken")

        #Team Selector
        ttk.Label(self, text="Team").grid(row=0, column=0, sticky="w", padx=8, pady=(2,2))
        self.team_dropdown_var = tk.StringVar()
        self.team_dropdown = ttk.OptionMenu(self, self.team_dropdown_var, "")
        self.team_dropdown.grid(row=1, column=0, sticky="ew", padx=8)
        
        #Player List Container
        self.player_list_frame = ttk.Frame(self,style="PlayerList.TFrame")
        self.player_list_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=(8,10))
        self.inner.rowconfigure(2, weight=1)
        self.inner.columnconfigure(0, weight=1)

        #Add and Remove Buttons
        self.add_btn = ttk.Button(self, text="Add", command=self.add_player)
        self.add_btn.grid(row=3, column=0, padx=8, pady=(6,4), sticky="ew")
        
        self.remove_btn = ttk.Button(self, text="Remove", command=self.remove_selected_player, state="disabled")
        self.remove_btn.grid(row=4, column=0, padx=8, pady=(0,8), sticky="ew")
        
        ttk.Separator(self, orient="horizontal").grid(row=5, column=0, padx=8, pady=(0,6), sticky="ew")
        
        self.rename_btn = ttk.Button(self, text="Rename Team", command=self.rename_team)
        self.rename_btn.grid(row=6, column=0, padx=9, pady=(0,10), sticky="ew")

        self.player_buttons = []
        self.selected_player_button = None #track selection

        self.refresh_team_dropdown()
        self.team_dropdown_var.trace_add("write", lambda *_: self.on_team_change())
        self.refresh_player_list()
        
    #Helper Functions 

    def labels(self):
        tn = self.controller.team_names
        return {"home": tn["home"].get(), "away": tn["away"].get()}
    
    def refresh_team_dropdown(self):
        labels = self.labels()
        menu = self.team_dropdown["menu"]
        menu.delete(0, "end")
        for key in self.controller.team_order:
            label=labels[key]
            menu.add_command(label=label, command=tk._setit(self.team_dropdown_var, label))
        current_key = self.controller.selected_team_key.get()
        self.team_dropdown_var.set(labels[current_key])

    def on_team_change(self):
        labels = self.labels()
        label = self.team_dropdown_var.get()
        key = next((k for k, v in labels.items() if v == label), "home")
        if key != self.controller.selected_team_key.get():
            self.controller.selected_team_key.set(key)
            self.refresh_player_list()

    def refresh_player_list(self):
        for w in self.player_list_frame.winfo_children():
            w.destroy()
        self.player_buttons.clear()
        self.selected_player_button=None
        if hasattr(self, "remove_btn"):
            self.remove_btn.configure(state="disabled")

        key = self.controller.selected_team_key.get()
        for role_or_name in self.controller.rosters[key]:
            b = ttk.Button(self.player_list_frame, text=role_or_name, style="Player.TButton")
            b.configure(command=lambda btn=b: self.select_player_button(btn))
            b.pack(fill="x", padx=6, pady=2)
            self.player_buttons.append(b)

    def set_card_colors(self, fill, border):
        self.card.configure(bg=fill, highlightbackground=border)

    #Button Handlers 
    
    def select_player_button(self, btn: ttk.Button):
        if self.selected_player_button is btn:
            btn.configure(style="Player.TButton")
            self.selected_player_button=None
            self.remove_btn.configure(state="disabled")
            return
        if self.selected_player_button is not None:
            try:
                self.selected_player_button.configure(style="Player.TButton")
            except:
                pass
        btn.configure(style="PlayerSelected.TButton")
        self.selected_player_button = btn
        self.remove_btn.configure(state="normal")

    def add_player(self):
        key = self.controller.selected_team_key.get()
        team_label = self.controller.team_names[key].get()
        positions = ["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"]
        res = add_player_modal(self, team_label, positions)
        if not res:
            return
        self.controller.rosters[key].append(res["name"])
        self.refresh_player_list()
        for btn in self.player_buttons:
            if btn.cget("text") == res["name"]:
                self.select_player_button(btn)
                break
        if hasattr(self.controller, "set_status"):
            self.controller.set_status(f"Added {res['name']} ({res['position']}) to {team_label}")
            
    def remove_selected_player(self):
        if not self.selected_player_button:
            return
        name = self.selected_player_button.cget("text")
        key = self.controller.selected_team_key.get()
        team_label = self.controller.team_names[key].get()
        if not confirm("confirm_remove_player", self, name=name, team=team_label):
            return
        try:
            self.controller.rosters[key].remove(name)
        except ValueError:
            pass
        self.selected_player_button=None
        if hasattr(self, "remove_btn"):
            self.remove_btn.configure(state="disabled")
        self.refresh_player_list()
  
    def rename_team(self):
        labels=self.labels()
        current_label=self.team_dropdown_var.get()
        team_key=next((k for k, v in labels.items() if v == current_label), "home")
        if hasattr(self.controller, "rename_team"):
            self.controller.rename_team(team_key)
        self.refresh_team_dropdown()
                


class StatusBar(ttk.Frame): 
    def __init__(self, parent): 
        super().__init__(parent)

        self.grid_propagate(False)
        self.configure(height = BAR_HEIGHT - 8)

        self.grid_columnconfigure(0, weight = 1)
        self.grid_columnconfigure(1, weight= 1)

        self.message_variable = tk.StringVar(value = "Ready.")
        ttk.Label(self, textvariable=self.message_variable).grid(
            row = 0, column = 0, padx = 10, pady = 6, sticky = "w")

    def set_status(self, text: str):
        self.message_variable.set(text)

                         
class DataBar(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.grid_propagate(False)
        self.configure(width=SIDE_WIDTH)

        self.grid_columnconfigure(0, weight=1)

        ttk.Label(self, text="Stats", anchor="center").grid(
            row=0, column=0, sticky="ew", padx=8, pady=(10,6)
        )
        self.home_section = self._make_team_section(self, team_key="home", row=1)
        self.away_section = self._make_team_section(self, team_key="away", row=2)

        for key, name_var in self.controller.team_names.items():
            name_var.trace_add("write", lambda *_, k=key: self._sync_heading(k))
        
        self._sync_heading("home")
        self._sync_heading("away")

        self.refresh_from_points(self.controller.data_points)

    def _make_team_section(self, parent, team_key: str, row: int):
        box = ttk.LabelFrame(parent, text="", padding = 8)
        box.grid(row=row, column=0, sticky="nsew", padx=8, pady=(0,8))
        box.grid_columnconfigure(1, weight=1)

        vars = { #Add more as development continues
            "shots": tk.IntVar(value=0),
            "made": tk.IntVar(value=0),
            "missed": tk.IntVar(value=0),
            "airball": tk.IntVar(value=0),
            "pct": tk.StringVar(value=0),   
        }
        vars["heading"] = tk.StringVar(value="")

        box.configure(labelwidget=ttk.Label(box, textvariable=vars["heading"]))

        r=0
        ttk.Label(box, text="Shots:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["shots"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="Made:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["made"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="Missed:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["missed"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="Airball:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["airball"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="FG%:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["pct"]).grid(row=r, column=1, sticky="e"); r+=1

        if not hasattr(self, "_team_vars"):
            self._team_vars = {}
        self._team_vars[team_key] = vars
        return box
    
    def _sync_heading(self, team_key: str):
        team_name = self.controller.team_names[team_key].get()
        self._team_vars[team_key]["heading"].set(f"{team_name} Stats")

    def refresh_from_points(self, points: list[dict]):
        stats = {
            "home": {"shots": 0, "made": 0, "missed": 0, "airball": 0},
            "away": {"shots": 0, "made": 0, "missed": 0, "airball": 0},
        }

        for p in points or []:
            team = p.get("team")
            if team not in stats:
                continue
            stats[team]["shots"] += 1
            if p.get("airball"):
                stats[team]["airball"] += 1
            if p.get("made"):
                stats[team]["made"] += 1
            else:
                stats[team]["missed"] += 1  # treat non-made as miss unless you separate airballs

        for team_key in ("home", "away"):
            s = stats[team_key]
            shots, made = s["shots"], s["made"]
            pct = f"{(made / shots) * 100:.1f}%" if shots else "-"
            vars = self._team_vars[team_key]
            vars["shots"].set(shots)
            vars["made"].set(made)
            vars["missed"].set(s["missed"])
            vars["airball"].set(s["airball"])
            vars["pct"].set(pct)