import tkinter as tk 
from tkinter import ttk, messagebox

from src.config import ICON_PNG, ICON_ICO
from src.user_interface.court_canvas import StartScreen, CourtScreen
from src.user_interface.court_frames import CourtFrame
from src.user_interface.player_dialogs import confirm_quit

class DunkVisionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dunk Vision")
        self.geometry("1024x576")
        self.minsize(854, 480)

        self.set_app_icon()
        self.protocol("WM_DELETE_WINDOW", self.on_app_close)
        self.init_styles

        self.option_add("*Button.Background", "#F3F5F7")
        self.option_add("*Button.Foreground", "#9DAFBF")
        self.option_add("*Button.ActiveBackground", "#F1F3F5")
        self.option_add("*Button.ActiveForeground", "#839AAF")

        self.root = ttk.Frame(self)
        self.root.grid(row = 0, column = 0, sticky = "nsew")
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)

        #Cause the Center to Grow
        self.root.grid_rowconfigure(1, weight = 1)
        self.root.grid_columnconfigure(1, weight = 1)

        #Bars
        self.topbar = TopBar(self.root)
        self.topbar.grid(row = 0, column = 0, columnspan = 3, sticky = "ew")
        
        self.sidebar = SideBar(self.root, controller = self)
        self.sidebar.grid(row = 1, column = 0, sticky = "ns")

        #Center - Starting with StartScreen, moving to CourtScreen
        self.center = StartScreen(self.root, controller = self)
        self.center.grid(row = 1, column = 1, sticky = "nsew")

        #Status Bar
        self.status = StatusBar(self.root)
        self.status.grid(row = 2, column = 0, columnspan = 3, sticky = "ew") 

        #TEST THIS FOR AESTHETICS - SPACER SO SIDEBAR DOESN'T HUG, MAYBE NOT NEEDED SINCE IMAGE HAS BUFFER BUILT-IN
        self.root.grid_columnconfigure(2, minsize = 8)   
                               
    def set_app_icon(self):
        try: 
            if ICON_ICO.exists():
                self.iconbitmap(str(ICON_ICO))
            if ICON_PNG.exists():
                png = tk.PhtoImage(file = str(ICON_PNG))
                self.icon_reference = png 
                self.iconphoto(True, png)
        except Exception as e:
            print(f"[Icon Warning] {e}")


    def show_start_screen(self):
        self.center.grid_forget()
        self.center = StartScreen(self.root, controller = self)
        self.center.grid(row = 1, column = 1, sticky = "nsew")


    def show_court_screen(self):
        self.center.grid_forget()
        self.center = CourtScreen(self.root, controller = self)
        self.center.grid(row = 1, column = 1, sticky = "nsew")


    def init_styles(self):
        style = ttk.Style(self)
        style.configure("TButton", padding = (12, 6))
        self.option_add("*Font", "Segoe UI 10")


    def on_app_close(self):
        if confirm_quit():
            self.destroy()