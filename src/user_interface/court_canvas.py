import tkinter as tk 
from tkinter import ttk, filedialog
from PIL import Image, ImageTk, ImageColor
from src.config import SCREEN_IMAGES_DIR
from pathlib import Path

NATIVE_WIDTH = 1366
NATIVE_HEIGHT = 768

class ScreenImage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0, bg="#230F1A")
        self.canvas.pack(fill="both", expand=True)

        self.images: dict[str, Image.Image] = {}
        self._photo: ImageTk.PhotoImage | None = None
        self._current_key: str | None = None
        self._last_size: tuple[int, int] = (0, 0)
        self._image_id: int | None = None

        self.load_image("start", "dv_start_screen.png")
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

    def _fit_image(self, src, target_width, target_height, mode="contain"):
        iw, ih = src.size
        if mode == "cover":
            target_ar = target_width / target_height
            image_ar = iw/ih
            if image_ar > target_ar:
                new_width = int(ih * target_ar)
                left = (iw - new_width) // 2
                box = (left, 0, left + new_width, ih)
            else: 
                new_height = int(iw / target_ar)
                top = (ih - new_height) // 2
                box = (0, top, iw, top + new_height)
            src = src.crop(box)
            return src.resize((target_width, target_height), Image.LANCZOS)
        scale = min(target_width / iw, target_height / ih)
        d_width, d_height = max(1, int(iw*scale)), max(1, int(ih*scale))
        return src.resize((d_width, d_height), Image.LANCZOS)

    def _render(self) -> None:
        if not self._current_key:
            return
        src = self.images.get(self._current_key)
        if src is None:
            self.canvas.delete("all")
            self._photo = None
            self._image_id = None
            return

        cw = max(self.canvas.winfo_width(),1)
        ch = max(self.canvas.winfo_height(),1)

        mode = "cover" if self._current_key == "start" else "contain"
        img = self._fit_image(src, cw, ch, mode=mode)

        iw, ih = img.size
        x = (cw - iw) // 2
        y = (ch - ih) // 2

        self._photo = ImageTk.PhotoImage(img)
        if self._image_id is None:
            self._image_id = self.canvas.create_image(x, y, anchor="nw", image=self._photo)
        else:
            self.canvas.coords(self._image_id, x, y)
            self.canvas.itemconfigure(self._image_id, image=self._photo)

    def export_png(self, path: str) -> bool: 
        try: 
            self.update_idletasks()
            src = self.images.get(self._current_key)
            if src is None: 
                print("[export_png] No current image set")
                return False
        
            width = max(self.canvas.winfo_width(), 1)
            height = max(self.canvas.winfo_height(), 1)

            scale = min(width / NATIVE_WIDTH, height / NATIVE_HEIGHT)
            d_w = max(1, int(NATIVE_WIDTH * scale))
            d_h = max(1, int(NATIVE_HEIGHT * scale))
            x = (width - d_w) // 2
            y = (height - d_h) // 2

            bg = self.canvas.cget("bg")

            try: 
                bg_rgb = ImageColor.getrgb(bg)
            except Exception: 
                try: 
                    r16, g16, b16 = self.winfo_rgb(bg)
                    bg_rgb = (r16//256, g16//256, b16//256)
                except Exception:
                    bg_rgb = (0, 0, 0)

            out = Image.new("RGB", (width, height), bg_rgb)
            resized = src.resize((d_w, d_h), Image.LANCZOS).convert("RGB")
            out.paste(resized, (x,y))
            out.save(path)

            return True 
             
        except Exception as e:
            print(f"[export_png] ERROR: {e!r}")
            return False



class StartScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller 
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.bg = ScreenImage(self)
        self.bg.grid(row=0, column=0, sticky="nsew")
        self.bg.show("start")

        self._BASE_WIDTH, self._BASE_HEIGHT = 1366, 768
        self._NEW_CX, self._NEW_CY = 566.5, 622.5
        self._LOAD_CX, self._LOAD_CY = 796.5, 622.5

        new_button = ttk.Button(self, text = "New", command = self.new_session)
        load_button = ttk.Button(self, text = "Load", command = self.load_session)

        self._new_win_id = self.bg.canvas.create_window(
            self._NEW_CX, self._NEW_CY, window = new_button, anchor="center"
        )
        self._load_win_id = self.bg.canvas.create_window(
            self._LOAD_CX, self._LOAD_CY, window = load_button, anchor="center"
        )

        self.bg.canvas.bind("<Configure>", self._position_buttons, add="+")
        self.after_idle(lambda: self._position_buttons(None))

        self.bg.show("start")

        self.bg.canvas.tag_raise(self._new_win_id)
        self.bg.canvas.tag_raise(self._load_win_id)

    def _position_buttons(self, event):
        c = self.bg.canvas
        cw, ch = c.winfo_width(), c.winfo_height()

        scale_x = cw / self._BASE_WIDTH
        scale_y = ch / self._BASE_HEIGHT
        scale = min(scale_x, scale_y)

        scaled_width = self._BASE_WIDTH * scale
        scaled_height = self._BASE_HEIGHT * scale

        offset_x = (cw - scaled_width) / 2.0
        offset_y = (ch - scaled_height) / 2.0

        new_x = offset_x + self._NEW_CX * scale 
        new_y = offset_y + self._NEW_CY * scale
        load_x = offset_x + self._LOAD_CX * scale
        load_y = offset_y + self._LOAD_CY *scale 

        c.coords(self._new_win_id, new_x, new_y)
        c.coords(self._load_win_id, load_x, load_y)
  

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