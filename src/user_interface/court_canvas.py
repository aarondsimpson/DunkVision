import tkinter as tk 
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
from src.config import SCREEN_IMAGES_DIR

NATIVE_WIDTH = 1366
NATIVE_HEIGHT = 768

class ScreenImage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg="#111")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.images = {} #Key -> PIL.Image
        self.tkref = None
        self.current = None

        #Preload Images
        self.load_image("start", "dv_start_screen_with_buttons.png")
        self.load_image("court_light", "court_light_mode.png")
        self.load_image("court_dark", "court_dark_mode.png")

        self.bind("<Configure>", lambda e: self.image_draw())

    def load_image(self, key, filename):
        path = SCREEN_IMAGES_DIR / filename
        if path.exists():
            self.images[key] = Image.open(path).convert("RGBA")
    
    def show(self, key: str):
        self.current=key
        self.image_draw()

    def image_draw(self):
        self.canvas.delete("all")
        image=self.images.get(self.current)
        if not image:
            return
        width, height=self.canvas.winfo_width(), self.canvas.winfo_height()
        if width < 2 or height <2:
            return 
        
        scale=min(width / NATIVE_WIDTH, height / NATIVE_HEIGHT)
        d_width, d_height=int(NATIVE_WIDTH*scale), int(NATIVE_HEIGHT*scale)
        x, y=(width - d_width) // 2, (height - d_height) // 2
        resized=image.resize((d_width, d_height), Image.LANCZOS) 
        self.tkref=ImageTk.PhotoImage(resized)
        self.canvas.create_image(x, y, anchor="nw", image=self.tkref)


class StartScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller 
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.bg = ScreenImage(self)
        self.bg.grid(row=0, column=0, sticky="nsew")
        self.bg.show("start")

        new_button = ttk.Button(self, text = "New", command = self.new_session)
        load_button = ttk.Button(self, text = "Load", command = self.load_session)

        new_button.place(relx=0.45, rely=0.62, anchor="center", width=120, height=40) #Later replace with image overlay
        load_button.place(relx=0.60, rely=0.62, anchor="center", width=120, height=40)#Later replace with image overlay

    def new_session(self):
        self.controller.show_court_screen() 


    def load_session(self):
        path = filedialog.askopenfilename(
            title = "Load a Dunk Vision Save",
            filetypes = [("Dunk Vision Save", "*.dvjson"), ("All Files", "*.*")]
        )
        """if path: 
            #CODE THIS LATER WHEN SAVE AND LOAD FUNCTIONS ARE BUILT
            self.controller.show_frame("CourtFrames")
            """

class CourtScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.bg = ScreenImage(self)
        self.bg.grid(row = 0, column = 0, sticky = "nsew")
        self.bg.show("court_dark")

        court_label = ttk.Label(self, text="Placeholder")
        court_label.grid(row=0, column=0, padx=20, pady=(60, 20), sticky = "nw")

        back_button = ttk.Button(self, text = "Home", command=self.controller.show_start_screen)
        back_button.grid(row=0, column=0, padx=20, pady=(60, 20), sticky="n")

