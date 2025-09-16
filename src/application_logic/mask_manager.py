from PIL import Image 
from src.application_logic.court_mask_color_ledger import ZONE_COLORS, LINE_COLORS, PLAY_COLORS, NO_CLICK_COLORS

class MaskManager: 
    def __init__(self, path: str): 
        with Image.open(path) as im:
            self.img = im.convert("RGBA").copy()
        self.px = self.img.load()

    def get_zone_at(self, ix: int, iy: int) -> tuple[str, str]: 
        w, h = self.img.width, self.img.height
        if not (0 <= ix < w and 0 <= iy < h):
            return ("OUT_OF_BOUNDS", "Out of Bounds")
    
        r, g, b, _ = self.px[ix, iy]
        rgb = (r, g, b)

        if rgb in LINE_COLORS: return ("LINE", ZONE_COLORS[rgb])
        if rgb in NO_CLICK_COLORS: return ("NO_CLICK", ZONE_COLORS[rgb])
        if rgb in ZONE_COLORS: return ("ZONE", ZONE_COLORS[rgb])
        return ("UNKNOWN", f"Unmapped color {rgb}")