from pathlib import Path
from src.application_logic.mask_manager import MaskManager
from src import config 

MASK_PATH = config.MASK_IMAGES_DIR / "court_mask.png"
if not MASK_PATH.is_file():
    raise FileNotFoundError(f"Court mask not found at {MASK_PATH}")
MASK = MaskManager(str(MASK_PATH))

COURT_WIDTH_FEET = 50.0 #High school court width
COURT_LENGTH_FEET = 50.0 #42ft for high school half, plus 6ft of half of center ring, plus 2ft to marker

HOOP_CENTER_X_FT = COURT_WIDTH_FEET / 2.0 
HOOP_CENTER_Y_FT = 4.0 

COURT_LEFT_PX = 340 #Spreads between 336 to 340 - Choosing the inside edge
COURT_RIGHT_PX = 1040 #Spreads between 1040 and 1044 - Choosing the inside edge 
COURT_BASELINE_Y_PX = 60 #Spreads between 57 and 60 - Choosing the inside edge 
COURT_FAR_EDGE_Y_PX = 765
HOOP_CX_PX = 690
HOOP_CY_PX = 139

W, H = MASK.img.width, MASK.img.height

def _use_defaults_if_missing():
    global COURT_LEFT_PX, COURT_RIGHT_PX, COURT_BASELINE_Y_PX, COURT_FAR_EDGE_Y_PX, HOOP_CX_PX, HOOP_CY_PX
    missing = any(v is None for v in(
        COURT_LEFT_PX, COURT_RIGHT_PX, COURT_BASELINE_Y_PX, COURT_FAR_EDGE_Y_PX, HOOP_CX_PX, HOOP_CY_PX
    ))
    if not missing: 
        return False
    
    if COURT_LEFT_PX is None: COURT_LEFT_PX = 0 
    if COURT_RIGHT_PX is None: COURT_RIGHT_PX = W - 1
    if COURT_BASELINE_Y_PX is None: COURT_BASELINE_Y_PX = 0 
    if COURT_FAR_EDGE_Y_PX is None: COURT_FAR_EDGE_Y_PX = H - 1 
    if HOOP_CX_PX is None: HOOP_CX_PX = W // 2
    if HOOP_CY_PX is None: HOOP_CY_PX = int(H * 0.18)
    print(
        "[DunkVision] Court bbox is not calibrated yet - using WHOLE-IMAGE defaults"
    )
    return True 

_boot_used_defaults = _use_defaults_if_missing()

COURT_SPAN_X_PX = abs(COURT_RIGHT_PX - COURT_LEFT_PX)
COURT_SPAN_Y_PX = abs(COURT_FAR_EDGE_Y_PX - COURT_BASELINE_Y_PX)

if COURT_SPAN_X_PX <= 0 or COURT_SPAN_Y_PX <= 0: 
    raise ValueError(
        "Court bbox spans must be positive"
        "Check COURT_LEFT/RIGHT_PX and BASELINE/FAR_EDGE_Y_PX"
    )

PPF_X = COURT_SPAN_X_PX / COURT_WIDTH_FEET
PPF_Y = COURT_SPAN_Y_PX / COURT_LENGTH_FEET

_Y_POSITIVE_IF_IF_INCREASES = 1 if (COURT_FAR_EDGE_Y_PX > COURT_BASELINE_Y_PX) else - 1

def is_in_court_bbox(ix: int, iy: int) -> bool:
    x_ok = (min(COURT_LEFT_PX, COURT_RIGHT_PX) <= ix <= max(COURT_LEFT_PX, COURT_RIGHT_PX))
    y_ok = (min(COURT_BASELINE_Y_PX, COURT_FAR_EDGE_Y_PX) <= iy <= max(COURT_BASELINE_Y_PX, COURT_FAR_EDGE_Y_PX))
    return x_ok and y_ok

def pixels_to_feet(ix: int, iy: int):
    x_ft = (ix - COURT_LEFT_PX) / PPF_X if COURT_RIGHT_PX >= COURT_LEFT_PX else (COURT_LEFT_PX - ix) / PPF_X

    if _Y_POSITIVE_IF_IF_INCREASES > 0: 
        y_ft = (iy - COURT_BASELINE_Y_PX) / PPF_Y
    else: 
        y_ft = (COURT_BASELINE_Y_PX - iy) / PPF_Y
    return x_ft, y_ft

def shot_distance_from_hoop(ix: int, iy: int):
    x_ft, y_ft = pixels_to_feet(ix, iy)
    dx_ft = x_ft - HOOP_CENTER_X_FT
    dy_ft = y_ft - HOOP_CENTER_Y_FT
    r_ft = (dx_ft**2 + dy_ft**2) ** 0.5
    return r_ft, dx_ft, dy_ft 