#STEP TWO 
#Define constants for COURT_LENGTH_FEET, COURT_HEIGHT_FEET
#Define constants for HOOP_CENTER_X, HOOP_CENTER_Y
#Define PIXELS_PER_FOOT = NATIVE_COURT_LENGTH_PIXELS / COURT_LENGTH_FEET 
#STEP THREE IN ZONING

#STEP FOUR
#Post-Mask-Creation: Map RGB coors to zone names and metadata(is3pt)
'''
ZONE_MAP = {
(255,0,0): {"name": "Left Corner", "is_3_point": True},
}
'''
#STEP FIVE IN ZONING

from application_logic.mask_manager import MaskManager

MASK_PATH = "assets/mask_images/court_mask.png"
MASK = MaskManager(MASK_PATH)