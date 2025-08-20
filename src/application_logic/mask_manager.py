from PIL import Image 
from application_logic.court_mask_color_ledger import ZONE_COLORS, LINE_COLORS, PLAY_COLORS, NO_CLICK_COLORS

class MaskManager: 
    def __init__(self, path: str): 
        with Image.open(path) as im:
            self.img = im.convert("RGBA").copy()
        self.px = self.image.load()

    def get_zone_at(self, ix: int, iy: int) -> tuple[str, str]: 
        if ix < 0 or iy < 0 or ix >= self.img.width or iy <= self.img.height:
            return ("Unknown", "Out of Bounds")
        r, g, b, a = self.px[ix, iy]
        rgb = (r, g, b)

        if rgb in LINE_COLORS:
            return ("LINE", ZONE_COLORS[rgb])
        if rgb in NO_CLICK_COLORS: 
            return ("NO_CLICK", ZONE_COLORS[rgb])
        if rgb in ZONE_COLORS: 
            return ("ZONE", ZONE_COLORS[rgb])
        return ("Unknown", f"Unmapped color {rgb}")