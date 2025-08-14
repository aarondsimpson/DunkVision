import tkinter as tk 
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
from src.config import SCREEN_IMAGES_DIR
from pathlib import Path

NATIVE_WIDTH = 1366
NATIVE_HEIGHT = 768

class ScreenImage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.images: dict[str, Image.Image] = {}
        self._photo: ImageTk.PhotoImage | None = None
        self._current_key: str | None = None
        self._last_size: tuple[int, int] = (0, 0)
        self._image_id: int | None = None

        self.load_image("start", "dv_start_screen_with_buttons.png")
        self.load_image("court_light", "court_light_mode.png")
        self.load_image("court_dark", "court_dark_mode.png")

        # Bind to the CANVAS so we catch real size changes
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def load_image(self, key: str, filename: str) -> None:
        path = SCREEN_IMAGES_DIR / filename
        try:
            if path.exists():
                self.images[key] = Image.open(path).convert("RGBA")
            else:
                print(f"[ScreenImage] Missing file: {path}")
        except Exception as e:
            print(f"[ScreenImage] Failed to load {path}: {e}")

    def show(self, key: str) -> None:
        self._current_key = key
        # Render after layout completes
        self.after_idle(self._render)

    def _on_canvas_configure(self, event) -> None:
        size = (event.width, event.height)
        if size != self._last_size:
            self._last_size = size
            if self._current_key:
                self._render()

    def _render(self) -> None:
        if not self._current_key:
            return
        src = self.images.get(self._current_key)
        if src is None:
            self.canvas.delete("all")
            self._photo = None
            self._image_id = None
            return

        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)

        scale = min(width / NATIVE_WIDTH, height / NATIVE_HEIGHT)
        d_w, d_h = max(1, int(NATIVE_WIDTH * scale)), max(1, int(NATIVE_HEIGHT * scale))
        x = (width - d_w) // 2
        y = (height - d_h) // 2

        resized = src.resize((d_w, d_h), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(resized)
        if self._image_id is None:
            self._image_id = self.canvas.create_image(x, y, anchor="nw", image=self._photo)
        else:
            self.canvas.coords(self._image_id, x, y)
            self.canvas.itemconfigure(self._image_id, image=self._photo)


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