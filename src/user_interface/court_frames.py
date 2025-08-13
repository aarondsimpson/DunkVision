import tkinter as tk
from tkinter import ttk
from src.user_interface.court_canvas import ScreenImage

BAR_HEIGHT = 44
SIDE_WIDTH = 220

MODE = {
    "light": {"image": "court_light", "bg": "#BCA382"},
    "dark": {"image": "court_dark", "bg": "#7C90C5"}
    }

class CourtFrame(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller=controller
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.topbar=TopBar(self, controller=self)
        self.topbar.grid(row=0, column=0, columnspan=3, sticky="ew")

        self.sidebar=SideBar(self, controller=self)
        self.sidebar.grid(row=1, column=0, sticky="ns")

        self.center_canvas=ScreenImage(self)
        self.center_canvas.grid(row=1, column=1, sticky="nsew")
        
        self.statusbar=StatusBar(self)
        self.statusbar.grid(row=2, column=0, columnspan=3, sticky="ew")

        self.mode = "dark"
        self.update_mode()

    def toggle_mode(self):
        self.mode="dark" if self.mode == "light" else "light"
        self.update_mode()

    def update_mode(self):
        cfg = MODE[self.mode]

        self.center_canvas.show(cfg["image"])

        style = ttk.Stle(self)
        style.configure("TopBar.TFrame", background = cfg["bg"])
        style.configure("SideBar.TFrame", background = cfg["bg"])
        style.configure("StatusBar.TFrame", background = cfg["bg"])

        self.topbar.configure(style="TopBar.Frame")
        self.sidebar.configure(style="SideBar.TFrame")
        self.statusbar.configure(style="StatusBar.TFrame")

    def home_button(self):
        pass

    def undo_action(self):
        pass

    def redo_action(self):
        pass

    def select_quarter(self):
        pass

    def save_game(self):
        pass

    def reset_game(self):
        pass

    def end_game(self):
        pass

    def export_image(self):
        pass
    
    def export_json(self):
        pass

    def export_csv(self):
        pass
     

class TopBar(ttk.Frame):
    def __init__(self, parent, controller = None):
        super().__init__(parent)
        self.controller = controller

        self.grid_propagate(False)
        self.configure(height = BAR_HEIGHT)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        self.title = ttk.Label(self, text="Dunk Vision")
        self.title.grid(row=0, column=0, padx=10, pady=8, sticky="w")


        #Theme Button
        ttk.Button(self, text = "Light/Dark", command = getattr(controller, "toggle_mode", lambda: None)).grid(
            row=0, column=0, padx=10, pady=(12, 6), sticky="ew"
        )
        #Home Button 
        ttk.Button(self, text="Home", command=getattr(controller, "home_button", lambda:None)).grid(
            row=0, column=0, padx=10, pady=(12, 6), sticky="ew"
        )

        #Undo Button
        ttk.Button(self, text="Undo", command=getattr(controller, "undo_action", lambda: None)).grid(
            row=0, column=1, padx=10, pady=(12, 6), sticky="n"
        )

        #Redo Button
        ttk.Button(self, text="Redo", command=getattr(controller, "redo_action", lambda: None)).grid(
            row=0, column=1, padx=10, pady=(12, 6), sticky="n"
        ) 

        #Quarter Block 
        ttk.Button(self, text="Q1", command=getattr(controller, "select_quarter", lambda: None)).grid(
            row=0, column=1, padx=10, pady=(12, 6), sticky="n"
        )
        ttk.Button(self, text="Q2", command=getattr(controller, "select_quarter", lambda: None)).grid(
            row=0, column=1, padx=10, pady=(12, 6), sticky="n"
        )
        ttk.Button(self, text="Q3", command=getattr(controller, "select_quarter", lambda: None)).grid(
            row=0, column=1, padx=10, pady=(12, 6), sticky="n"
        )
        ttk.Button(self, text="Q4", command=getattr(controller, "select_quarter", lambda: None)).grid(
            row=0, column=1, padx=10, pady=(12, 6), sticky="n"
        )

        #Game Save
        ttk.Button(self, text="Save", command=getattr(controller, "save_game", lambda: None)).grid(
            row=0, column=1, padx=10, pady=(12, 6), sticky="n"
        )

        #Game Reset
        ttk.Button(self, text="Reset", command=getattr(controller, "reset_game", lambda: None)).grid(
            row=0, column=1, padx=10, pady=(12, 6), sticky="n"
        )

        #Game End
        ttk.Button(self, text="End Game", command=getattr(controller, "end_game", lambda: None)).grid(
            row=0, column=1, padx=10, pady=(12, 6), sticky="n"
        )

        #Export Buttons
        ttk.Button(self, text="Image", command=getattr(controller, "export_image", lambda: None)).grid(
            row=0, column=2, padx=10, pady=(12, 6), sticky="n"
        )
        ttk.Button(self, text="JSON", command=getattr(controller, "export_json", lambda: None)).grid(
            row=0, column=2, padx=10, pady=(12, 6), sticky="n"
        )
        ttk.Button(self, text="CSV", command=getattr(controller, "export_csv", lambda: None)).grid(
            row=0, column=2, padx=10, pady=(12, 6), sticky="n"
        )
       

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
        
        #Home and Away Rosters
        self.rosters={
            "My Team": ["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"],
            "Their Team":["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"],
        }
        #Player list container
        self.player_list_frame = tk.Frame(self.sidebar, bg="#BF9F8F")
        self.player_list_frame.grid(row=1, column=0, sticky="nsew", pady=(10,10))

        #Subframe for holding default player buttons 
        self.player_buttons = []
        self.selected_player_button = None #track selection

        #Add ADD PLAYER button 
        self.add_button = tk.Button(self.sidebar, text="Add", command=self.add_player_dialog)
        self.add_button.grid(row=2, column=0, pady=5, sticky="ew")
        
        #Add REMOVE PLAYER button
        self.remove_button = tk.Button(self.sidebar, text="Remove", state="disabled", command=self.remove_selected_player)
        self.remove_button.grid(row=3, column=0, pady=5, sticky="ew")

        #Populate initial list and team switch 
        self.refresh_player_list()
        self.selected_team.trace_add("write", lambda *_: self.on_team_change())
        
        self.player_btn_bg = "#e9e9e9"
        self.player_btn_selected_bg = "#ffd966"
        self.player_buttons = []
        self.selected_player_button = None


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

                         
