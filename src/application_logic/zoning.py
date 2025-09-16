from src.application_logic.zoning_configuration import MASK
from src.application_logic.court_mask_color_ledger import(
    ZONE_COLORS, LINE_COLORS, PLAY_COLORS, NO_CLICK_COLORS
)

def resolve_zone(ix: int, iy: int):
    kind, name = MASK.get_zone_at(ix, iy)
    return kind.lower(), name