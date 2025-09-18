from __future__ import annotations
import sys
from pathlib import Path

def _app_root() -> Path: 
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]

#Root Paths
ROOT_DIR: Path = _app_root()

#Asset Paths
ASSETS_DIR = ROOT_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
SCREEN_IMAGES_DIR = ASSETS_DIR / "screen_images"
MASK_IMAGES_DIR = ASSETS_DIR / "mask_images"
FONTS_DIR = ASSETS_DIR / "fonts"

#Icon Image Paths
ICON_PNG = ICONS_DIR / "dv_app_icon.png"
ICON_ICO = ICONS_DIR / "dv_app_icon.ico"

#Session Data Paths
USER_HOME_BASE = Path.home() / "DunkVision"
SESSION_DATA_DIR = USER_HOME_BASE / "session_data"
PLAYER_PROFILES_DIR = SESSION_DATA_DIR / "player_profiles"
SESSION_PROFILES_DIR = SESSION_DATA_DIR / "session_profiles"
TMP_DIR = SESSION_DATA_DIR / "tmp"

#Optional Paths for CourtFrame
SAVES_DIR = USER_HOME_BASE / "saves"
EXPORTS_DIR = USER_HOME_BASE / "exports"

#Check Directories Exist (Safe No-Op)
for directory in (
    USER_HOME_BASE, 
    SESSION_DATA_DIR, PLAYER_PROFILES_DIR, SESSION_PROFILES_DIR, TMP_DIR, 
    SAVES_DIR, EXPORTS_DIR,
):
    directory.mkdir(parents=True, exist_ok=True)

def resource_path(*parts: str | Path) -> Path: 
    return ROOT_DIR.joinpath(*parts)