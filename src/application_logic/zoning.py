#STEP THREE
#def pixels_to_feet(ix, iy): convert ix, iy to dx, dy from hoop center in feet. 
#Compute Euclidean distance sqrt(dx*dx + dy*dy), return: distance_feet, dx_ft, dy_ft). 
#STEP FOUR IN ZONING CONFIG AFTER BUILDING MASKS (BUILD MASKS FOR NO CLICK ZONE)

#STEP FIVE
#Load masks as PIL.Image -> .load() pixel array. 
'''def get_zone(ix, iy)
    color=mask_pixels[ix, iy][:3]
    return ZONE_MAP.get(color, {"name": "Unknown", "is_3_point": None})
'''
#STEP SIX IN COURT_INTERACTIVITY

from application_logic.zoning_configuration import MASK
from application_logic.court_mask_color_ledger import(
    ZONE_COLORS, LINE_COLORS, PLAY_COLORS, NO_CLICK_COLORS
)

def resolve_zone(ix: int, iy: int):
    r, g, b, _ = MASK.px[ix, iy]
    rgb = MASK.get_zone_at(ix, iy)

    if rgb in LINE_COLORS: return "line", LINE_COLORS[rgb]
    if rgb in NO_CLICK_COLORS: return "no_click", NO_CLICK_COLORS[rgb]
    if rgb in PLAY_COLORS: return "play", PLAY_COLORS[rgb]
    return "unknown", f"{rgb}"