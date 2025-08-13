import tkinter as tk
from tkinter import ttk
from src.user_interface.court_canvas import ScreenImage

BAR_HEIGHT = 44
SIDE_WIDTH = 220

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
        self.mode="dark"

        self.statusbar=StatusBar(self)
        self.statusbar.grid(row=2, column=0, columnspan=3, sticky="ew")

        self.center_canvas.show("court_dark")

    def toggle_mode(self): 
        self.mode = "dark" if self.mode == "light" else "light"
        key = "court_dark" if self.mode == "dark" else "court_light"
        self.center_canvas.show(key)

    def update_mode(self):
        key = "court_dark" if self.mode == "dark" else "court_light"
        self.center_canvas.show(key)

        """Style colors for light mode: ---

        bg_color = "#F3F5F7" if self.mode == "light" else "#222"
        self.topbar.configure(style = "TopBar.TFrame")
        self.sidebar.configure(style = "SideBar.TFrame")
        self.statusbar.configure(self = "StatusBar.TFrame")
        
        """

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

        self.theme_btn=ttk.Button(
            self, 
            text="Theme",
            command=self.controller.toggle_mode if hasattr(self.controller, "toggle_mode") else lambda: None
        )
        self.theme_btn.grid(row=0, column=2, padx=10, pady=8, sticky="e")

class SideBar(ttk.Frame):
    def __init__(self, parent, controller = None): 
        super().__init__(parent)
        self.controller = controller

        self.grid_propagate(False)
        self.configure(width = SIDE_WIDTH)

        ttk.Button(self, text = "Light/Dark", command = getattr(controller, "toggle_mode", lambda: None)).grid(
            row = 0, column = 0, padx = 10, pady = (12, 6), sticky = "ew"
        )

        self.grid_rowconfigure(99, weight = 1)

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

                         
