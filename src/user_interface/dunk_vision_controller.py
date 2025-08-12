import tkinter as tk 
from tkinter import ttk, filedialog

from src.config import ICON_PNG, ICON_ICO
from src.user_interface.court_canvas import StartScreen

class DunkVisionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dunk Vision")
        self.geometry("1024x576")
        self.minsize(854, 480)
        self.set_app_icon()

        self.option_add("*Button.Background", "#F3F5F7")
        self.option_add("*Button.Foreground", "#9DAFBF")
        self.option_add("*Button.ActiveBackground", "#F1F3F5")
        self.option_add("*Button.ActiveForeground", "#839AAF")

        container = ttk.Frame(self)
        container.grid(row = 0, column = 0, sticky = "nsew")
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)

        self.frames = {}

        for Frames in (start_screen):
            frame = Frames(parent = container, controller = self)
            frame.grid(row = 0, column = 1, sticky = "nsew")
            self.frames[Frames.__name__] = frame 
        
        self.init_styles()
        self.show_frame("start_screen")


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


    def show_frame(self, name: str):
        self.frames[name].tkraise()

