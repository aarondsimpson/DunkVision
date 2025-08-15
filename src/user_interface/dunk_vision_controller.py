from pathlib import Path
import sys
import tkinter as tk 
from tkinter import ttk, font as tkfont
from PIL import Image, ImageTk

from src.config import ICON_PNG, ICON_ICO
from src.user_interface.court_canvas import StartScreen, CourtScreen
from src.user_interface.court_frames import TopBar, SideBar, StatusBar, CourtFrame
from src.user_interface.player_dialogs import confirm

class DunkVisionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dunk Vision")

        if sys.platform.startswith("win"):
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"com.dunkvision.app")
            except Exception:
                pass

            ico = Path(ICON_ICO)
            png = Path(ICON_PNG)
            self._icon_refs = {}
            
            if sys.platform.startswith("win") and ico.is_file():
                try: 
                    self.iconbitmap(str(ico))
                except tk.TclError: 
                    pass
            if png.is_file():
                try: 
                    self._icon_refs["app_png"] = tk.PhotoImage(file=str(png))
                    self.wm_iconphoto(True, self._icon_refs["app_png"])
                except tk.TclError:
                    pass

        self.restore_geometry="1024x576+100+100"
        self.minsize(854, 480)

        try: 
            self.state('zoomed')
        except tk.TclError: 
            self.update_idletasks()
            screen_width=self.winfo_screenwidth()
            screen_height=self.winfo_screenheight()
            self.geometry(f"{screen_width}x{screen_height}+0+0")

        self.update_idletasks()
        self.previous_state=self.state()
        self.bind("<Configure>", self.on_configure_state_change)

        self.set_app_icon()
        self.protocol("WM_DELETE_WINDOW", self.on_app_close)
        self.init_styles()

        self.option_add("*Button.Background", "#F3F5F7")
        self.option_add("*Button.Foreground", "#9DAFBF")
        self.option_add("*Button.ActiveBackground", "#F1F3F5")
        self.option_add("*Button.ActiveForeground", "#839AAF")

        self.root=ttk.Frame(self)
        self.root.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        #Cause the Center to Grow
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        #Center - Starting with StartScreen, moving to CourtScreen
        self.center=StartScreen(self.root, controller=self)
        self.center.grid(row=1, column=1, sticky="nsew")

                              
    def set_app_icon(self):
        base = Path(__file__).resolve().parent.parent
        ico = base / "assets" / "icons" / "dv_app_icon.ico"
        png = base / "assets" / "icons" / "dv_app_icon.png"

        if sys.platform.startswith("win") and ico.exists(): 
            self.iconbitmap(str(ico))
        elif png.exists():
            self.iconphoto(True, ImageTk.PhotoImage(Image.open(png)))
        


    def on_configure_state_change(self, _):
        current=self.state()
        if current != self.previous_state:
            if self.prevous_state == "zoomed" and current == "normal":
                self.geometry(self.restore_geometry)
            self.prevous_state=current


    def show_start_screen(self):
        self.center.grid_forget()
        self.center=StartScreen(self.root, controller=self)
        self.center.grid(row=1, column=1, sticky="nsew")


    def show_court_screen(self):
        self.center.grid_forget()
        self.center=CourtFrame(self.root, controller=self)
        self.center.grid(row=1, column=1, sticky="nsew")


    def init_styles(self):
        style=ttk.Style(self)
        style.configure("TButton", padding=(12, 6))

        base = tkfont.nametofont("TkDefaultFont")
        base.configure(family="Segoe UI", size=10)
        self.option_add("*Font", base)
        self.option_add("*TButton.Font", base)
      
      
    def on_app_close(self):
        if confirm("quit"):
            self.destroy()

    
    def go_home(self):
        self.show_start_screen()