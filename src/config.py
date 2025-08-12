from pathlib import Path

#Root Paths
ROOT_DIR = Path(__file__).resolve().parents[1]

#Asset Paths
ASSETS_DIR = ROOT_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
SCREEN_IMAGES_DIR = ASSETS_DIR / "screen_images"
MASK_IMAGES_DIR = ASSETS_DIR / "mask_images"
FONTS_DIR = ASSETS_DIR / "fonts"

#Session Data Paths
SESSION_DATA_DIR = ROOT_DIR / "session_data"
PLAYER_PROFILES_DIR = SESSION_DATA_DIR / "player_profiles"
SESSION_PROFILES_DIR = SESSION_DATA_DIR / "session_profiles"
TMP_DIR = SESSION_DATA_DIR / "tmp"

#Icon Image Paths
ICON_PNG = ICONS_DIR / "dv_app_icon.png"
ICON_ICO = ICONS_DIR / "dv_app.icon.ico"

#Check Directories Exist (Safe No-Op)
for directory in [
    ASSETS_DIR, ICONS_DIR, SCREEN_IMAGES_DIR, MASK_IMAGES_DIR, FONTS_DIR, 
    SESSION_DATA_DIR, PLAYER_PROFILES_DIR, SESSION_PROFILES_DIR, TMP_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)