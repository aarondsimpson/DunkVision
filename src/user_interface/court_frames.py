import json 
import csv
import tkinter as tk

from tkinter import ttk, filedialog
from PIL import ImageGrab

from src.user_interface.court_canvas import ScreenImage
from src.user_interface.player_dialogs import confirm, info
from src.user_interface.modals import add_player_dialog

BAR_HEIGHT = 44
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
        self.controller=controller
        
        #State Definition 
        self.mode="dark"
        self.quarter=tk.StringVar(value="Q1")
        self.actions=[]
        self.redo_stack=[]
        self.data_points=[]

        #Layout Scaffold
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        #Wdiget Scaffold
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
        self.topbar.grid(row=0, column=0, columnspan=3, sticky="ew")

        self.sidebar=SideBar(self, controller=self)
        self.sidebar.grid(row=1, column=0, sticky="ns")

        self.center_canvas=ScreenImage(self)
        self.center_canvas.grid(row=1, column=1, sticky="nsew")
        
        self.statusbar=StatusBar(self)
        self.statusbar.grid(row=2, column=0, columnspan=3, sticky="ew")
      

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

        self.topbar.configure(style="TopBar.Frame")
        self.sidebar.configure(style="SideBar.TFrame")
        self.statusbar.configure(style="StatusBar.TFrame")

    def home_button(self):
        if confirm("confirm_home",parent=self):
            if hasattr(self.cotroller, "go home") and callable(self.controller.go_home):
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
        path = filedialog.asksaveasfilnename(
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
        super().__init__(parent)
        self.grid_propagate(False)
        self.configure(height = BAR_HEIGHT)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        left=ttk.Frame(self)
        left.grid(row=0,column=0, sticky="w", padx=8, pady=6)

        ttk.Label(left, text="Dunk Vision").grid(row=0, column=0, padx=(0,8))
        ttk.Button(left, text="Home", command=on_home_button or (lambda:None)).grid(row=0, column=1, padx=3)
        ttk.Button(left, text="Light/Dark", command=on_toggle_mode or (lambda:None)).grid(row=0, column=2, padx=3)

        mid=ttk.Frame(self)
        mid.grid(row=0, column=1, sticky="n", pady=6)

        ttk.Button(mid, text="Undo", command=on_undo_action or (lambda:None)).grid(row=0, column=0, padx=3)
        ttk.Button(mid, text="Redo", command=on_redo_action or (lambda:None)).grid(row=0, column=1, padx=3)

        qvar=quarter_var or tk.StringVar(value="Q1")
        for index, quarter in enumerate(("Q1", "Q2", "Q3", "Q4"), start=0):
            ttk.Radiobutton(
                mid, text=quarter, value=quarter, variable=qvar,
                command=(lambda qq=quarter: (on_select_quarter or (lambda _q: None))(qq))
            ).grid(row=0, column=2+index, padx=3)
        
        right=ttk.Frame(self)
        right.grid(row=0, column=2, sticky="e", padx=8, pady=6)

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
        self.grid_propagate(False)
        self.configure(width = SIDE_WIDTH)

        #Team Selector
        self.selected_team = tk.StringVar(value="My Team")
        team_dropdown = ttk.OptionMenu(
            self.sidebar,
            self.selected_team,
            "My Team", 
            "My Team",
            "Their Team"
        )
        team_dropdown.grid(row=0, column=0, pady=(10, 5), sticky = "ew")
        
        #Player List Container
        self.player_list_frame = ttk.Frame(self,style="PlayerList.TFrame")
        self.player_list_frame.grid(row=1, column=0, sticky="nsew", pady=(10,10))

        #Add and Remove Buttons
        ttk.Button(self, text="Add", command=self.add_player_dialog).grid(row=2, column=0, pady=5, sticky="ew")
        ttk.Button(self, text="Remove", command=self.remove_selected_player).grid(row=3, column=0, pady=5, sticky="ew")

        #Home and Away Rosters
        self.rosters={
            "My Team": ["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"],
            "Their Team":["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"],
        }
        self.player_buttons = []
        self.selected_player_button = None #track selection

        #Populate Initial List and Team Switch 
        self.selected_team.trace_add("write", lambda *_: self.on_team_change())
        self.refresh_player_list()
        
    def refresh_player_list(self):
        for w in self.player_list_frame.winfo_children():
            w.destroy()
        for role in self.rosters[self.selected_team.get()]:
            b = ttk.Button(self.player_list_frame, text=role)
            b.pack(fill="x", padx=6, pady=2)
            self.player_buttons.append(b)


    def on_team_change(self):
        self.refresh_player_list()

    def add_player_dialog(self):
        team = self.selected_team.get()
        positions = self.roster.get(team, [])
        res = add_player_dialog(self, team, positions)
        if not res:
            return
        self.rosters[team].append(res["name"])
        self.refresh_player_list()
        if hasattr(self.controller, "set_status"):
            self.controller.set_status(f"Added {res['name']} ({res['position']}) to {team}")
            
    def remove_selected_player(self):
        if not self.selected_player_button:
            return
        name = self.selected_player_button.cget("text")
        team = self.selected_team.get()
        if not confirm("confirm_remove_player", self, name=name, team=team):
            return
        try:
            self.rosters[team].remove(name)
        except ValueError:
            pass
        self.refresh_player_list()

class StatusBar(ttk.Frame): 
    def __init__(self, parent): 
        super().__init__(parent)

        self.grid_propagate(False)
        self.configure(height = BAR_HEIGHT - 8)

        self.grid_columnconfigure(0, weight = 0)
        self.grid_columnconfigure(1, weight= 1)

        self.message_variable = tk.StringVar(value = "Ready.")
        ttk.Label(self, textvariable=self.message_variable).grid(
            row = 0, column = 0, padx = 10, pady = 6, sticky = "w")

    def set_status(self, text: str):
        self.message_variable.set(text)

                         
