import json 
import csv
import tkinter as tk
import os 
import uuid
from datetime import datetime
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from pathlib import Path

from src.user_interface.court_canvas import ScreenImage
from src.user_interface.player_dialogs import confirm, info, error, resolve, confirm_action, shots_assigned
from src.user_interface.modals import (add_player_dialog as add_player_modal, rename_team_dialog, manage_teams_modal, manage_players_dialog,
                                       shot_result_dialog, dunk_or_layup_dialog, choose_one_dialog, free_throw_reason_dialog)
from src.application_logic.zoning import resolve_zone
from src.application_logic.zoning_configuration import shot_distance_from_hoop 
from session_data import team_store as TS
from src import config
from session_data.game_io import write_game, read_game
from project import slugify

BAR_HEIGHT = 60
SIDE_WIDTH = 300
DEFAULT_ROSTER = [
    "Point Guard", 
    "Shooting Guard", 
    "Small Forward", 
    "Power Forward", 
    "Center"
]

MODE = {
    "light": {
        "image": "court_light", 
        "bg": "#8A6E53",
        "list": "#BCA382"},
    "dark": {
        "image": "court_dark", 
        "bg": "#41597F",
        "list": "#41597F",
    }}

SCHEMA_VERSION = "dv_shots_v1"
MAKE_TOKENS = {"make", "and1_make"}

def short_zone(label: str) -> str:
    if not label: 
        return "-"
    base, sep, suffix = label.partition(" - ")
    repl = {
        "Left": "L",
        "Right": "R",
        "Outside": "Outside",
        "Wing": "Wing",
        "Corner": "Corner",
        "Top of Key": "Top of Key",
        "High Post": "High Post",
        "Low Post": "Low Post",
        "Free Throw": "FT Line",
        "Above Break": "AB",
    }
    for k, v in repl.items():
        base = base.replace(k, v)
    return base + (f" - {suffix}" if sep else "")

def _points_from_zone(result: str, zone_name: str) -> int:
    """Infer points using only result + zone label (e.g., 'Right Slot - 3', 'Free Throw Line - 1')."""
    if str(result).strip().lower() not in MAKE_TOKENS:
        return 0
    z = str(zone_name or "").strip().lower()
    if "free throw line" in z:
        return 1
    if z.endswith("- 3"):
        return 3
    return 2

def _truthy(x) -> bool:
    if isinstance(x, bool):
        return x
    if x is None:
        return False
    return str(x).strip().lower() in {"true", "1", "yes", "y"}

class CourtFrame(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller= controller or self
        self.game_date = None
        self.game_location = None
        
        self.mode="dark"
        self.quarter=tk.StringVar(value="Q1")
        self.actions=[]
        self.redo_stack=[]
        self.data_points=[]
        self.team_order=["home","away"]
        
        self.team_names={
            "home": tk.StringVar(value="My Team"),
            "away": tk.StringVar(value="Their Team")
        }
        self.rosters={
            "home": list(DEFAULT_ROSTER),
            "away": list(DEFAULT_ROSTER),
        }
        self.selected_team_key=tk.StringVar(value="home")

        self.home_score = tk.IntVar(value=0)
        self.away_score = tk.IntVar(value=0)

        self._player_ids = {}

        self.player_roles = {"home": {}, "away": {}}
        for side in ("home", "away"):
            for name in self.rosters[side]:
                if name in DEFAULT_ROSTER:
                    self.player_roles[side][name] = name

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=SIDE_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        self.topbar=TopBar(
            self, 
            on_toggle_mode=self.toggle_mode,
            on_home_button=self.home_button,
            on_undo_action=self.undo_action,
            on_redo_action=self.redo_action,
            on_select_quarter=self.select_quarter,
            on_save_game=self.save_game,
            on_reset_game=self.reset_game, 
            on_export_image=self.export_image,
            on_export_csv=self.export_csv,
            on_export_json=self.export_json,
            quarter_var=self.quarter, 
            home_score_var = self.home_score,
            away_score_var = self.away_score,
            home_name_var = self.team_names["home"],
            away_name_var = self.team_names["away"],
            )
        self.topbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0,4))

        self.sidebar=SideBar(self, controller=self)
        self.sidebar.grid(row=1, column=0, sticky="nsew")

        self.center_canvas=ScreenImage(self)
        self.center_canvas.grid(row=1, column=1, sticky="nsew")

        c = self.center_canvas.canvas
        self._shot_markers: list[dict] = []
        
        c.bind("<Button-1>", self._on_canvas_click, add="+")     
        c.bind("<Configure>", lambda e: self.after_idle(self._reposition_markers), add="+")

        self.databar = DataBar(self, controller=self)
        self.databar.grid(row=1, column=2, sticky="ns")

        self.statusbar=StatusBar(self)
        self.statusbar.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(4,0))

        self.after_idle(self.update_mode)
        self.refresh_stats()   

    def _reposition_markers(self):
        if getattr(self.center_canvas, "_draw_info", None) is None: 
            self.after_idle(self._reposition_markers)
            return
        
        c = self.center_canvas.canvas
        r = 4
        for m in self._shot_markers:
            pos = self.center_canvas.image_to_canvas(m["ix"], m["iy"])
            if not pos: 
                continue 
            cx, cy = pos 
            c.coords(m["id"], cx - r, cy - r, cx + r, cy + r)

        c.tag_raise("shot_marker")

    def toggle_mode(self):
        self.mode="dark" if self.mode == "light" else "light"
        self.update_mode()
        self.set_status(f"Theme: {self.mode.title()}")
        
    def update_mode(self):
        cfg = MODE[self.mode]
        self.center_canvas.show(cfg["image"])
        self.after_idle(self._reposition_markers)

        style = ttk.Style(self)
        style.configure("TopBar.TFrame", background = cfg["bg"])
        style.configure("SideBar.TFrame", background = cfg["bg"])
        style.configure("StatusBar.TFrame", background = cfg["bg"])
        style.configure("DataBar.TFrame", background = cfg["bg"])

        self.topbar.configure(style="TopBar.TFrame")
        self.sidebar.configure(style="SideBar.TFrame")
        self.statusbar.configure(style="StatusBar.TFrame")
        self.databar.configure(style="DataBar.TFrame")

        if self.mode == "dark":
            self.sidebar.set_card_colors(fill="#E8EDF6", border="#A8B3C5")
        else: 
            self.sidebar.set_card_colors(fill="#EFE9DD", border="#BDAA90")

    def home_button(self):
        if confirm("confirm_home",parent=self):
            if hasattr(self.controller, "go_home") and callable(self.controller.go_home):
                self.controller.go_home()
            else:
                info("Not Wired", self, "Home navigation is not wired yet.")
        
    def _action_label(self, kind: str, *, prefix: str) -> str:                           
        mapping = {                                                                      
            "shot": "Shot",                                                              
            "add_player": "Add Player",                                                  
            "remove_player": "Remove Player",                                            
        }                                                                                
        base = mapping.get(kind, kind.title())                                           
        return f"{prefix} {base}"

    def undo_action(self):
        if not self.actions:
            self.set_status("Nothing to Undo.")
            return

        last = self.actions[-1]
        if not confirm_action("confirm_action", self,
                            action=self._action_label(last.get("type","action"), prefix="Undo")):
            return

        action = self.actions.pop()
        self.redo_stack.append(action)

        if action.get("type") == "shot":
            point = action.get("data")
            for i in range(len(self.data_points) - 1, -1, -1):
                if self.data_points[i] is point or self.data_points[i] == point:
                    self.data_points.pop(i)
                    break

            mid = action.get("marker_id")
            if mid:
                try:
                    self.center_canvas.canvas.delete(mid)
                except Exception:
                    pass
                self._shot_markers = [m for m in self._shot_markers if m.get("id") != mid]

            self.refresh_stats()
            self.set_status("Undid: shot")
            self.center_canvas.canvas.tag_raise("shot_marker")

        elif action.get("type") == "add_player":                                       
            team = action["team"]; name = action["name"]; idx = action.get("index")    
            roster = self.rosters.get(team, [])                                        
            try:                                                                       
                if idx is not None and 0 <= idx < len(roster) and roster[idx] == name:
                    roster.pop(idx)                                                    
                else:
                    roster.remove(name)                                                
            except ValueError:
                pass
            if self.selected_team_key.get() != team:                                   
                self.selected_team_key.set(team)                                       
                self.sidebar.refresh_team_dropdown()                                   
            self.sidebar.refresh_player_list()                                         
            self.set_status(f"Undid: Add Player ({name})")                             

        elif action.get("type") == "remove_player":                                    
            team = action["team"]; name = action["name"]; idx = action.get("index")    
            roster = self.rosters.get(team, [])

            ins = idx if isinstance(idx, int) and 0 <= idx <= len(roster) else len(roster)
            roster.insert(ins, name)  

            for p in action.get("shot_refs", []):
                try:
                    if p.get("team") == team:
                        p["player"] = name
                except Exception:
                    pass

            if self.selected_team_key.get() != team:                                   
                self.selected_team_key.set(team)                                       
                self.sidebar.refresh_team_dropdown()                                   
            self.sidebar.refresh_player_list()       
            self.refresh_stats()     

            cnt = len(action.get("shot_refs", []) or [])
            if cnt: 
                self.set_status(
                    f"Undid: Remove Player ({name}) - Reassigned {cnt} shot{'s' if cnt != 1 else ''}"
                )  
            else:
                self.set_status(f"Undid: Remove Player ({name})")                          

        
    def redo_action(self):
        if not self.redo_stack:
            self.set_status("Nothing to Redo.")
            return

        nxt = self.redo_stack[-1]
        if not confirm_action("confirm_action", self,
                            action=self._action_label(nxt.get("type","action"), prefix="Redo")):
            return

        action = self.redo_stack.pop()
        self.actions.append(action)

        if action.get("type") == "shot":
            point = action.get("data")
            self.data_points.append(point)

            mm = action.get("marker_meta") or {}
            ix, iy = mm.get("ix"), mm.get("iy")
            made = mm.get("made")
            team = mm.get("team")
            if None not in (ix, iy) and team is not None and made is not None:
                marker = self._draw_marker(ix, iy, made=made, team=team)
                if marker:
                    action["marker_id"] = marker["id"]

            self.refresh_stats()
            self.set_status("Redid: shot")
            self.center_canvas.canvas.tag_raise("shot_marker")

        elif action.get("type") == "add_player":                                       
            team = action["team"]; name = action["name"]; idx = action.get("index")    
            roster = self.rosters.get(team, [])
            ins = idx if isinstance(idx, int) and 0 <= idx <= len(roster) else len(roster)
            if name not in roster:
                roster.insert(ins, name)                                               
            if self.selected_team_key.get() != team:                                   
                self.selected_team_key.set(team)                                       
                self.sidebar.refresh_team_dropdown()                                   
            self.sidebar.refresh_player_list()                                         
            self.set_status(f"Redid: Add Player ({name})")                             

        elif action.get("type") == "remove_player":                                    
            team = action["team"]; name = action["name"]; idx = action.get("index")    
            roster = self.rosters.get(team, [])
           
            try:
                if idx is not None and 0 <= idx < len(roster) and roster[idx] == name:
                    roster.pop(idx)                                                    
                else:
                    roster.remove(name)                                                
            except ValueError:
                pass

            for p in action.get("shot_refs", []):
                try:
                    if p.get("team") == team: 
                        p["player"] = "Unassigned"
                except Exception: 
                    pass

            if self.selected_team_key.get() != team:                                   
                self.selected_team_key.set(team)                                       
                self.sidebar.refresh_team_dropdown()                                   
            self.sidebar.refresh_player_list()  
            self.refresh_stats()    

            cnt = len(action.get("shot_refs", []) or [])
            if cnt: 
                self.set_status(
                    f"Redid: Remove Player ({name}) - set {cnt} shot{'s' if cnt != 1 else ''} to 'Unassigned'"
                )
            else: 
                self.set_status(f"Redid: Remove Player ({name})")                          


    def select_quarter(self, q:str):
        self.quarter.set(q)
        self.set_status(f"Quarter: {q}")
                
    def save_game(self):
        default = "game.dvg.json"
        path = filedialog.asksaveasfilename(
            defaultextension=".dvg.json",
            filetypes=[("DunkVision Game (*.dvg.json)", "*.dvg.json"), ("JSON", "*.json")],
            title="Save Game",
            initialfile=default,
        )
        if not path:
            return
        try:
            write_game(Path(path), self)
            self.set_status(f"Saved: {path}")
        except Exception as e:
            messagebox.showerror("Save Failed", f"{e}")
            self.set_status("Save failed.")

    def load_game_dict(self, data: dict):
        ui = data.get("ui", {})
        self.mode = ui.get("mode", self.mode)
        self.quarter.set(ui.get("quarter", "Q1"))
        try: 
            self.selected_team_key.set(ui.get("selected_team_key", "home"))
        except Exception: 
            pass
        scores = ui.get("scores", {}) or {}
        self.home_score.set(int(scores.get("home", 0)))
        self.away_score.set(int(scores.get("away", 0)))

        t = data.get("teams", {}) or {}
        self.team_order = list(t.get("order", ["home", "away"]))
        names = t.get("names", {}) or {}
        for k in ("home", "away"):
            if k in self.team_names and k in names:
                self.team_names[k].set(names[k])
        rosters = t.get("rosters", {}) or {}
        for k in ("home", "away"):
            self.rosters[k] = list(rosters.get(k, self.rosters[k]))

        self.data_points = list(data.get("shots", []) or [])

        h = data.get("history", {}) or {}
        has_history = bool(h)
        self.actions = list(h.get("actions", []))
        self.redo_stack = list(h.get("redo_stack", []))
        
        for m in getattr(self, "_shot_markers", []):
            try: 
                self.center_canvas.canvas.delete(m["id"])
            except Exception: 
                pass
        self._shot_markers = []

        self.update_mode()
        self.after_idle(self._redraw_all_markers)
        self.after_idle(self._attach_marker_ids_to_history)

        if hasattr(self.sidebar, "refresh_team_dropdown"):
            self.sidebar.refresh_team_dropdown()
        if hasattr(self.sidebar, "refresh_player_list"):
            self.sidebar.refresh_player_list()
        
        self.refresh_stats()
        self.set_status("Game loaded.")     


    def _attach_marker_ids_to_history(self):
        if not self.data_points:
            return 
        
        def sig_xymt(obj):
            return (obj.get("x"), obj.get("y"),
                    obj.get("team"), bool(obj.get("made")))

        markers_by_sig: dict[tuple, list[int]] = {}
        for m in self._shot_markers:
            markers_by_sig.setdefault(
                (m.get("ix"), m.get("iy"), m.get("team"), bool(m.get("made"))), []
            ).append(m.get("id"))

        assigned = [None] * len(self.data_points)
        for i, p in enumerate(self.data_points):
            s = sig_xymt(p)
            bucket = markers_by_sig.get(s, [])
            assigned[i] = bucket.pop(0) if bucket else None

        if not self.actions:
            self.actions = []
            for i, p in enumerate(self.data_points):
                self.actions.append({
                    "type": "shot",
                    "data": p,
                    "marker_id": assigned[i],
                    "marker_meta": {
                        "ix": p.get("x"), "iy": p.get("y"),
                        "made": bool(p.get("made")),
                        "team": p.get("team", "home"),
                    },
                    "data_index": i,
                })
            self.redo_stack.clear()
            return

        used: set[int] = set()
        point_sigs = [sig_xymt(p) for p in self.data_points]
            
        for a in self.actions:
            if a.get("type") != "shot":
                continue
            pdata = a.get("data") or {}

            idx = a.get("data_index")
            if isinstance(idx, int) and 0 <= idx < len(assigned) and idx not in used:
                a["marker_id"] = assigned[idx]
                a["marker_meta"] = {
                    "ix": pdata.get("x"), "iy": pdata.get("y"),
                    "made": bool(pdata.get("made")),
                    "team": pdata.get("team", "home"),
                }
                used.add(idx)
                continue
            
            s = sig_xymt(pdata)
            for i, ps in enumerate(point_sigs):
                if i in used:
                    continue
                if ps == s:
                    a["marker_id"] = assigned[i]
                    a["marker_meta"] = {
                        "ix": pdata.get("x"), "iy": pdata.get("y"),
                        "made": bool(pdata.get("made")),
                        "team": pdata.get("team", "home"),
                    }
                    used.add(i)
                    break

    def apply_loaded_state(self, state: dict):
        try:
            self.game_date = state.get("game_date")
            self.game_location = state.get("game_location")
            self.mode = state.get("mode", "dark")
            self.quarter.set(state.get("quarter", "Q1"))
            self.actions = state.get("actions", [])
            self.redo_stack = state.get("redo_stack", [])
            self.data_points = state.get("data_points", [])
            self.team_order = state.get("team_order", ["home", "away"])
            for k, name in state.get("team_names", {}).items():
                if k in self.team_names:
                    self.team_names[k].set(name)
            self.rosters = state.get("rosters", {"home": list(DEFAULT_ROSTER), "away": list(DEFAULT_ROSTER)})

            self._shot_markers.clear()
            self.center_canvas.show(MODE[self.mode]["image"])
            for p in self.data_points:
                ix, iy = p.get("x"), p.get("y")
                made, team = p.get("made"), p.get("team")
                if ix is not None and iy is not None and team:
                    self._draw_marker(ix, iy, made=made, team=team)

            self.refresh_stats()
            self.set_status("Session restored.")
        except Exception as e:
            self.set_status(f"Failed to restore: {e}")


    def reset_game(self):
        if not confirm("confirm_reset", self):
            return    
        self.actions.clear()
        self.redo_stack.clear()
        self.data_points.clear()
        self.center_canvas.show(MODE[self.mode]["image"])
        self.refresh_stats()
        self.set_status("Reset.")

        for m in getattr(self, "_shot_markers", []):
            try: 
                self.center_canvas.canvas.delete(m["id"])
            except Exception:
                pass
        self._shot_markers.clear()


    def _normalize_shot_for_export(self, s: dict, *, export_timestamp: str, game_id: str) -> dict:
        zone_name = s.get("zone") or s.get("zone_name") or "" 
       
        shot_result = (s.get("result") or s.get("shot_result") or "").strip().lower()
        if not shot_result: 
            if s.get("made"):
                shot_result = "and1_make" if s.get("and1") else "make"
            else: 
                shot_result = "miss" 

        shot_points = s.get("shot_points")
        if shot_points in (None, ""):
            shot_points = _points_from_zone(shot_result, zone_name)
        try:
            shot_points = int(shot_points)
        except Exception:
            shot_points = 0
        made_bool = bool(shot_points > 0)

        raw_team = (s.get("team") or s.get("team_side") or "").strip().lower()
        if raw_team in ("home", "my"):
            team_side = "my"
        elif raw_team in ("away", "their"):
            team_side = "their"
        else:
            team_side = ""

        home_label = self.team_names["home"].get()
        away_label = self.team_names["away"].get()
        if team_side == "my":
            row_team_name = home_label
            row_opp_name  = away_label
        elif team_side == "their":
            row_team_name = away_label
            row_opp_name  = home_label
        else:
            row_team_name = getattr(self, "team_name", "") or s.get("team_name", "")
            row_opp_name  = getattr(self, "opponent_team_name", "") or s.get("opponent_team_name", "")

        period = s.get("period")
        if not period:
            q = str(s.get("quarter", "")).upper().lstrip()
            period = q or ""

        if s.get("player") and not s.get("player_id"):
            key = (s.get("team"), s.get("player"))
            s["player_id"] = self._player_ids.setdefault(key, str(uuid.uuid4()))

        player_id   = s.get("player_id")   or s.get("shooter_id")   or ""
        player_name = s.get("player_name") or s.get("shooter_name") or s.get("player") or ""
        player_role = (
            s.get("player_role") or s.get("role") or
            self.player_roles.get(s.get("team") or "", {}).get(player_name, "")
        )        

        team_slug = slugify(row_team_name)
        opp_slug = slugify(row_opp_name)
        player_slug = slugify(player_name)
        
        shot_context = s.get("shot_context") or s.get("made_context") or ""
        miss_context = s.get("miss_context") or ("Airball" if s.get("airball") else "")

        ft_bool = s.get("free_throw_bool")
        if ft_bool is None:
            ft_bool = "free throw line" in str(zone_name).strip().lower()
        else:
            ft_bool = _truthy(ft_bool)

        if ft_bool:
            ft_type = str(s.get("free_throw_type") or s.get("ft_reason") or "Free Throw") if ft_bool else "zero"

            if made_bool and not shot_context:
                shot_context = "Free Throw"
            elif not made_bool and not miss_context:
                miss_context = "Free Throw"
        else:
            ft_type = "zero"


        raw_shot_type = (s.get("shot_type") or "").strip()

        if ft_bool:
            shot_type = "Free Throw"
        elif raw_shot_type:
            shot_type = raw_shot_type
        else:
            zlow = str(zone_name).strip().lower()
            if "dunk" in zlow:
                shot_type = "Dunk"
            elif "layup" in zlow:
                shot_type = "Layup"
            else:
                shot_type = "Field Goal"

        shot_type = (s.get("shot_type") or shot_type or "Field Goal")

        distance_ft = s.get("distance_ft")
        if distance_ft in (None, ""):
            distance_ft = s.get("r_ft", "")
        try:
            distance_ft = float(distance_ft) if distance_ft not in (None, "") else None
        except Exception:
            distance_ft = None


        def _num(x):
            try:
                return float(x)
            except Exception:
                return None
            
        x_court = s.get("x_court")
        if x_court in (None, ""):
            x_court = s.get("x")
        x_court = _num(x_court) if x_court not in (None, "") else None

        y_court = s.get("y_court")
        if y_court in (None, ""):
            y_court = s.get("y")
        y_court = _num(y_court) if y_court not in (None, "") else None 


        return {
            "schema_version":   SCHEMA_VERSION,
            "export_timestamp": export_timestamp,
            "game_id":          game_id,
            "shot_id":          s.get("shot_id") or str(uuid.uuid4()),

            "team_side":        team_side,
            "team_name":        row_team_name,
            "team_name_slug":   team_slug,
            "opponent_team_name": row_opp_name,
            "opponent_team_slug": opp_slug,
            "period":           period,

            "player_id":        player_id,
            "player_name":      player_name,
            "player_slug":      player_slug,
            "player_role":      player_role,

            "shot_result":      shot_result,
            "shot_points":      shot_points,
            "made_bool":        bool(made_bool),
            "shot_type":        shot_type,

            "shot_context":     shot_context,
            "miss_context":     miss_context,
            "free_throw_bool":  bool(ft_bool),
            "free_throw_type":  ft_type,

            "zone_name":        zone_name,
            "distance_ft":      distance_ft,
            "x_court":          x_court,
            "y_court":          y_court,
    }

    def export_image(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")],
            title="Export Court Image",
        )
        if not path: 
            return
        
        ok = self.center_canvas.export_png(path)
        p = Path(path)
    
        if ok and p.exists():
            self.set_status(f"Image Exported: {p}")
            title, msg = resolve("export_success", path=p)
            messagebox.showinfo(title, msg)
        else: 
            self.set_status("Export Failed.")
            title, msg = resolve("export_fail", path=p)
            messagebox.showerror(title, msg)

    def export_json(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            title="Export Data (JSON)",
        )
        if not path:
            return

        shots = list(getattr(self, "data_points", []) or [])

        export_timestamp = datetime.now().isoformat(timespec="seconds")
        game_date        = getattr(self, "game_date", "") or getattr(self, "session_date", "")
        game_location    = getattr(self, "game_location", "")
        game_id          = getattr(self, "game_id", "") or str(uuid.uuid4())

        normalized_shots = [
            self._normalize_shot_for_export(s, export_timestamp=export_timestamp, game_id=game_id)
            for s in shots
        ]

        payload = {
            "schema_version": SCHEMA_VERSION,
            "export_timestamp": export_timestamp,

            "game": {
                "game_id": game_id,
                "game_date": game_date,
                "game_location": game_location,
            },

            "teams": {
                "order": list(self.team_order),
                "names": {
                    "home": self.team_names["home"].get(),
                    "away": self.team_names["away"].get(),
                },
                "slugs": {
                    "home": slugify(self.team_names["home"].get()),
                    "away": slugify(self.team_names["away"].get()),
                },
                "rosters": {
                    "home": list(self.rosters.get("home", [])),
                    "away": list(self.rosters.get("away", [])),
                },
            },

            "ui": {
                "mode": self.mode,
                "quarter": self.quarter.get(),
                "selected_team_key": self.selected_team_key.get(),
                "scores": {
                    "home": int(self.home_score.get() if self.home_score else 0),
                    "away": int(self.away_score.get() if self.away_score else 0),
                },
            },
            "shots": normalized_shots,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        if not getattr(self, "game_id", None):
            try:
                self.game_id = game_id
            except Exception:
                pass

        try:
            self.set_status(f"JSON Exported: {path}")
        except Exception:
            print(f"JSON Exported: {path}")


    def export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Export Data (CSV)",
        )
        if not path:
            return

        shots = list(getattr(self, "data_points", []) or [])

        export_timestamp = datetime.now().isoformat(timespec="seconds")
        game_date        = getattr(self, "game_date", "") or getattr(self, "session_date", "")
        game_location    = getattr(self, "game_location", "")
        team_name        = getattr(self, "team_name", "") or getattr(self, "my_team_name", "")
        opponent_name    = getattr(self, "opponent_team_name", "") or getattr(self, "their_team_name", "")
        game_id          = getattr(self, "game_id", "") or str(uuid.uuid4())           
        
        normalized_shots = [
            self._normalize_shot_for_export(s, export_timestamp=export_timestamp, game_id=game_id)
            for s in shots
        ]

        cols = [
            "schema_version","export_timestamp","game_date","game_location","game_id","shot_id",
            "team_side","team_name","opponent_team_name","period", "team_slug", "opp_slug", 
            "player_id","player_name","player_role", "player_slug",
            "shot_result","shot_points","made_bool", "shot_type",
            "shot_context","miss_context","free_throw_bool","free_throw_type",
            "zone_name","distance_ft","x_court","y_court",
        ]         

        out_rows = []
        for n in normalized_shots:
            out = {

                "schema_version":   SCHEMA_VERSION,
                "export_timestamp": export_timestamp,
                "game_date":        game_date,
                "game_location":    game_location,

                "game_id":          n["game_id"],
                "shot_id":          n["shot_id"],
                "team_side":        n["team_side"],
                "team_name":        n["team_name"],
                "team_slug":        n["team_slug"],
                "opponent_team_name": n["opponent_team_name"],
                "opp_slug":         n["opp_slug"],
                "period":           n["period"],
                "player_id":        n["player_id"],
                "player_name":      n["player_name"],
                "player_slug":      n["player_slug"],
                "player_role":      n["player_role"],
                "shot_result":      n["shot_result"],
                "shot_points":      n["shot_points"],
                "made_bool":        "TRUE" if n["made_bool"] else "FALSE",
                "shot_type":        n["shot_type"],
                "shot_context":     n["shot_context"],
                "miss_context":     n["miss_context"],
                "free_throw_bool":  "TRUE" if n["free_throw_bool"] else "FALSE",
                "free_throw_type":  n["free_throw_type"],
                "zone_name":        n["zone_name"],
                "distance_ft":      "" if n["distance_ft"] is None else n["distance_ft"],
                "x_court":          "" if n["x_court"] is None else n["x_court"],
                "y_court":          "" if n["y_court"] is None else n["y_court"],
            }
            out_rows.append({k: out.get(k, "") for k in cols})

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            writer.writeheader()
            if out_rows:
                writer.writerows(out_rows)

        if not getattr(self, "game_id", None):
            try: self.game_id = game_id
            except Exception: pass
        try: 
            self.set_status(f"CSV Exported: {path}")
        except Exception: 
            print(f"CSV Exported: {path}")
        
    def set_status(self, text: str):
        if hasattr(self.statusbar, "set_status"):
            self.statusbar.set_status(text)

    def rename_team(self, team_key: str):
        if team_key not in self.team_names:
            self.set_status(f"Unknown Team Key: {team_key}")
            return
            
        current = self.team_names[team_key].get()

        new_name = rename_team_dialog(self, current)
        if not new_name or new_name == current: 
            return
        new_name = (str(new_name) or "").strip()
        
        def _norm(s: str) -> str:
            return (s or "").strip().casefold()

        try:
            all_saved = TS.list_teams()
            existing = next((t for t in all_saved if _norm(t.team_name) == _norm(new_name)), None)
        except Exception:
            try:
                t = TS.get_team_by_name(new_name)
                existing = t
            except Exception:
                existing = None


        if existing: 
            use_saved = messagebox.askyesno(
                "Team Already Saved", 
                (f"A saved team named '{new_name}' already exists.\n\n"
                 f"Do you want to use the existing team for this side?\n\n"
            ))
            if use_saved: 
                try:
                    self.team_names[team_key].set(existing.team_name)
                    self.rosters[team_key] = list(existing.roster or [])
                except Exception: 
                    pass

            if hasattr(self.sidebar, "refresh_team_dropdown"):
                    self.sidebar.refresh_team_dropdown()
            if hasattr(self.databar, "_sync_heading"):
                    try:
                        self.databar._sync_heading(team_key)
                    except Exception:
                        pass
            self.set_status(f"Applied saved team: {existing.team_name}")
            return
        
        overwrite = messagebox.askyesno(
            "Overwrite Saved Team?", 
            (f' Do you want to overwrite the saved roster for "{new_name}"'
             f'with the current roster?\n\n'
             f'Yes - Overwrite saved roster\nNo = Keep Both(Auto-Suffix Name)')
            )
        if overwrite:
            try:
                TS.upsert_team(team_name=new_name, roster=list(self.rosters.get(team_key, [])))
                self.team_names[team_key].set(new_name)
            except Exception:
                pass

            if hasattr(self.sidebar, "refresh_team_dropdown"):
                self.sidebar.refresh_team_dropdown()
            if hasattr(self.databar, "_sync_heading"):
                try:
                    self.databar._sync_heading(team_key)
                except Exception:
                    pass
            self.set_status(f"Overwrote saved team: {new_name}")
            return
        
        base = new_name
        suffix = 2
        while True:
            candidate = f"{base} ({suffix})"
            try:
                clash = TS.get_team_by_name(candidate)
            except Exception:
                clash = None
            if not clash:
                new_name = candidate
                break
            suffix += 1

        self.team_names[team_key].set(new_name)

        if hasattr(self.sidebar, "refresh_team_dropdown"):
            self.sidebar.refresh_team_dropdown()
        if hasattr(self.databar, "_sync_heading"):
            try:
                self.databar._sync_heading(team_key)
            except Exception:
                pass

        self.set_status(f"Team Renamed: {current} → {new_name}")

    def refresh_stats(self):
        if hasattr(self, "databar") and hasattr(self.databar, "refresh_from_points"):
            self.databar.refresh_from_points(self.data_points)

    def record_shot(self, *, team: str, x: int, y: int, 
                    made: bool, airball: bool=False, 
                    meta: dict|None=None,
                    status_text: str | None=None):
                
        point = {
            "team": team, 
            "x": int(x), "y": int(y),
            "made": bool(made), "airball": bool(airball),
            "quarter": self.quarter.get(),
        }
        if meta: point.update(meta)

        pn = (meta or {}).get("player")
        pid = self._player_ids.setdefault((team, pn), str(uuid.uuid4()))
        point["player_id"] = pid

        self.data_points.append(point)
        self.actions.append({"type": "shot", "data": point})
        self.redo_stack.clear()
        self.refresh_stats()

        if status_text is None: 
            team_name = self.team_names[team].get()
            outcome = "Made" if made else ("Airball" if airball else "Missed")
            self.set_status(f"Recorded Shot: {team_name} - {outcome} (Q{self.quarter.get()[-1]}, x:{x}, y:{y})")
        else: 
            self.set_status(status_text)

    def _on_canvas_click(self, event):
        mapped = self.center_canvas.canvas_to_image(event.x, event.y)
        if mapped is None:
            self.set_status("Click outside image.")
            return 
        
        ix, iy = mapped
        
        kind, label = resolve_zone(ix, iy)
        kind_norm = str(kind).lower().replace(" ", "_")
        zone_lower = (label or "").strip().lower()
      
        is_dunk_zone = (kind_norm in {"dunk_zone", "dunk"} or "dunk" in zone_lower)  
        is_free_throw = (kind_norm in {"free_throw", "free_throw_line"}            
                         or "free throw" in zone_lower)                             

        if kind_norm == "no_click" and not is_free_throw: 
            self.set_status(f"{label} - not a playable zone.")
            return 
        if kind_norm in ("out_of_bounds", "unknown"):
            self.set_status(label)
            return 
        
        player_name = self.sidebar.get_selected_player_name()
        if not player_name:
            self.set_status("Select a player first.")
            return 
        
        res = shot_result_dialog(self, show_and1=not is_free_throw)
        if res is None: 
            return
      
        made = bool(res["made"])
        and1 = bool(res.get("and1", False))

        shot_kind = None
        made_context = None
        missed_context = None
        ft_reason = None

        if is_free_throw:
            ft_reason = free_throw_reason_dialog(parent = self)
            if ft_reason is None:
                return
            if made: 
                made_context = "Free Throw"
            else: 
                missed_context = "Free Throw"
        else: 
            if is_dunk_zone: 
                shot_kind = dunk_or_layup_dialog(parent = self)
                if shot_kind is None:
                    return

            if made: 
                made_context = choose_one_dialog(
                    parent = self, 
                    title="Made Shot Context",
                    prompt="How was it made?",
                    options=["Assisted", "Iso", "From Rebound"],
                )
                if made_context is None: 
                    return
            else:
                missed_context = choose_one_dialog(
                    parent = self,
                    title="Missed Shot Context",
                    prompt="Missed — Choose One:",
                    options=["Airball", "Rebounded"],
            )
                if missed_context is None:
                    return 

                
        r_ft, dx_ft, dy_ft = shot_distance_from_hoop(ix, iy)
        team_key = self.selected_team_key.get()        
        marker = self._draw_marker(ix, iy, made=made, team=team_key)

        team_name = self.team_names[team_key].get()
        tail_bits = []
        if shot_kind: tail_bits.append(shot_kind)
        if is_free_throw: tail_bits.append(f"Free Throw ({ft_reason})")
        if and1 and not is_free_throw: tail_bits.append("And-1")
        if made_context:     tail_bits.append(made_context)
        if missed_context:   tail_bits.append(missed_context)
        tail = f" [{', '.join(tail_bits)}]" if tail_bits else ""
        
        status_text = (
        f"{team_name}: {player_name} - {label} - {r_ft:.1f} ft "
        f"(Q{self.quarter.get()[-1]}){tail}"
        )

        meta = {
            "player": player_name, "zone": label,
            "zone_key": str(kind),
            "r_ft": r_ft, "dx_ft": dx_ft, "dy_ft": dy_ft,
        }
        if not is_free_throw and and1:
            meta["and1"] = True
        if shot_kind: 
            meta["shot_type"] = shot_kind
        if made_context:     
            meta["made_context"] = made_context 
        if missed_context:   
            meta["miss_context"] = missed_context 
        if is_free_throw:    
            meta["shot_type"] = "Free Throw"
            meta["ft_reason"] = ft_reason         

        self.record_shot(
            team=team_key, 
            x=ix, y=iy, 
            made=made, airball=(missed_context == "Airball") if not is_free_throw else False,
            meta=meta, status_text=status_text)
        
        try:
            if marker and self.actions and self.actions[-1].get("type") == "shot":
                self.actions[-1]["marker_id"] = marker["id"]
                self.actions[-1]["marker_meta"] = {
                    "ix": ix, "iy": iy, "made": made, "team": team_key
            }
        except Exception:
            pass
             
    def _draw_marker(self, ix: int, iy: int, *, made:bool, team: str):
        pos = self.center_canvas.image_to_canvas(ix, iy)
        if not pos: 
            return 
       
        cx, cy = pos 
        r = 4
        fill = "#3F704D" if made else "#960018"

        if team == "home": 
            cid = self.center_canvas.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r, 
                outline="", fill=fill, 
                tags=("shot_marker", "home_marker"),    
            )
            shape = "oval"
        else:       
            cid = self.center_canvas.canvas.create_rectangle(
            cx - r, cy - r, cx + r, cy + r, 
            outline="", fill=fill, 
            tags=("shot_marker", "away_marker")
       )
            shape = "rectangle"

        self.center_canvas.canvas.tag_raise(cid)
        m = {"id": cid, "ix": ix, "iy": iy, "made": made, "team": team, "shape": shape}
        self._shot_markers.append(m)
        return m 

    def _redraw_all_markers(self):
        if getattr(self.center_canvas, "_draw_info", None) is None:
            self.after_idle(self._redraw_all_markers)
            return
        
        for m in getattr(self, "_shot_markers", []):
            try: 
                self.center_canvas.canvas.delete(m["id"])
            except Exception:
                pass
        self._shot_markers = []

        self.center_canvas.show(MODE[self.mode]["image"])

        for p in self.data_points or []:
            ix, iy = p.get("x"), p.get("y")
            made = bool(p.get("made"))
            team = p.get("team")
            if ix is not None and iy is not None and team in ("home", "away"):
                self._draw_marker(ix, iy, made=made, team=team)

        self.center_canvas.canvas.tag_raise("shot_marker")
        self.after_idle(self._reposition_markers)

    def get_selected_player(self) -> str | None:
        try:
            return self.sidebar.get_selected_player_name()
        except Exception:
            return None


class TopBar(ttk.Frame):
    def __init__(
            self, parent, 
            on_toggle_mode=None, on_home_button=None,
            on_undo_action=None, on_redo_action=None, 
            on_select_quarter=None,
            on_save_game=None, on_reset_game=None,  
            on_export_image=None, on_export_json=None, on_export_csv=None,
            quarter_var: tk.StringVar | None=None,
            home_score_var: tk.IntVar | None=None, 
            away_score_var: tk.IntVar | None=None,
            home_name_var: tk.StringVar | None=None,
            away_name_var: tk.StringVar | None=None, 
    ):              
        super().__init__(parent, padding=(8, 10))
        self.grid_propagate(False)
        self.configure(height = BAR_HEIGHT)

        icon_path = os.path.join(config.ASSETS_DIR, "icons", "dv_app_icon.png")
        icon_img = Image.open(icon_path).resize((24,24), Image.LANCZOS)
        self.icon_photo = ImageTk.PhotoImage(icon_img)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        left=ttk.Frame(self)
        left.grid(row=0,column=0, sticky="w", padx=8)

        ttk.Label(left, image=self.icon_photo).grid(row=0, column=0, padx=(0,8))
        ttk.Button(left, text="Home", command=on_home_button or (lambda:None)).grid(row=0, column=1, padx=3)
        ttk.Button(left, text="Theme", command=on_toggle_mode or (lambda:None)).grid(row=0, column=2, padx=3)

        mid=ttk.Frame(self)
        mid.grid(row=0, column=1, sticky = "nsew", pady=6) 
        mid.grid_propagate(True)

        ttk.Button(mid, text="Undo", command=on_undo_action or (lambda:None)).grid(row=0, column=0, padx=3)
        ttk.Button(mid, text="Redo", command=on_redo_action or (lambda:None)).grid(row=0, column=1, padx=3)

        quarters = ("Q1", "Q2", "Q3", "Q4")
        qvar=quarter_var or tk.StringVar(value="Q1")
        base_column = 2
        for index, quarter in enumerate(quarters):
            ttk.Radiobutton(
                mid, text=quarter, value=quarter, variable=qvar,
                command=(lambda qq=quarter: (on_select_quarter or (lambda _q: None))(qq))
            ).grid(row=0, column= base_column +index, padx=3)

        sb_col = base_column + len(quarters)
        mid.grid_columnconfigure(sb_col, weight =1)
        
        sb = ttk.Frame(mid, padding =(8, 0))
        sb.grid(row=0, column=sb_col, padx=(12,3), sticky="nsew")
        sb.grid_rowconfigure(0, weight = 1)
        sb.grid_rowconfigure(2, weight = 1)

        hscore = home_score_var or tk.IntVar(value=0)
        ascore = away_score_var or tk.IntVar(value=0)

        ttk.Label(sb, text="My Team").grid(row=0, column=0, padx=(0,4))
        ttk.Label(sb, textvariable=hscore, font=("TkDefaultFont", 10, "bold")).grid(row=0, column=1)
        ttk.Label(sb, text="-").grid(row=0, column=2, padx=4)
        ttk.Label(sb, textvariable=ascore, font=("TkDefaultFont", 10, "bold")).grid(row=0, column=3)
        ttk.Label(sb, text="Their Team").grid(row=0, column=4, padx=(4,0))


        right=ttk.Frame(self)
        right.grid(row=0, column=2, sticky="e", padx=8)
        
        ttk.Button(right, text="Save", command=on_save_game or (lambda:None)).grid(row=0, column=0, padx=3)
        ttk.Button(right, text="Reset", command=on_reset_game or (lambda:None)).grid(row=0, column=1, padx=3)

        ttk.Button(right, text="Export Image", command=on_export_image or (lambda:None)).grid(row=0, column=2, padx=(16,3))
        ttk.Button(right, text="Export JSON", command=on_export_json or (lambda:None)).grid(row=0, column=3, padx=3)
        ttk.Button(right, text="Export CSV", command=on_export_csv or (lambda:None)).grid(row=0, column=4, padx=3)


class SideBar(ttk.Frame):
    def __init__(self, parent, controller = None): 
        super().__init__(parent)
        self.controller = controller
        self.grid_propagate(False)
        self.configure(width = SIDE_WIDTH, padding=0)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text="Select Team", anchor="center").grid(
            row=0, column=0, sticky="ew", padx=8, pady=(10,6)
        )

        self.card = tk.Frame(
            self, 
            bg = "#E8EDF6",
            highlightthickness=1,
            highlightbackground= "#A8B3C5",
        )
        self.card.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,8))
        self.inner = ttk.Frame(self.card, padding=8, style="CardInner.TFrame")
        self.inner.pack(fill="both", expand=True)

        style=ttk.Style(self)
        style.configure("Player.TButton", padding=4)
        style.configure("PlayerSelected.TButton", padding=4, relief="sunken")

        self.team_dropdown_var = tk.StringVar()
        self.team_dropdown = ttk.OptionMenu(self.inner, self.team_dropdown_var, "")
        self.team_dropdown.grid(row=1, column=0, sticky="ew", padx=8)

        self._make_scrollable_player_list(self.inner)                      
        self.inner.rowconfigure(2, weight=1)                               
        self.inner.columnconfigure(0, weight=1) 

        self.manage_btn = ttk.Button(self.inner, text="Manage Players", command=self.manage_players)
        self.manage_btn.grid(row=3, column=0, padx=8, pady=(8,10), sticky="ew")
        
        self.player_buttons = []
        self.selected_player_button = None 
        self.selected_player_name = None
        self.selected_player_var = tk.StringVar(value="")
        self.selected_player_var.trace_add("write", lambda *_: (
            hasattr(self.controller, "refresh_stats") and self.controller.refresh_stats()
        ))

        self.refresh_team_dropdown()
        self.team_dropdown_var.trace_add("write", lambda *_: self.on_team_change())
        self.refresh_player_list() 

    def _make_scrollable_player_list(self, parent):                          
        container = ttk.Frame(parent, style="PlayerList.TFrame")             
        container.grid(row=2, column=0, sticky="nsew", padx=8, pady=(8,10))  

        # Scrollbar on the LEFT
        vbar = ttk.Scrollbar(container, orient="vertical")               
        vbar.grid(row=0, column=0, sticky="ns")                               

        self._pl_canvas = tk.Canvas(
            container, highlightthickness=0, bd=0,
            background=self.card.cget("bg"),
            yscrollcommand=vbar.set
        )
        self._pl_canvas.grid(row=0, column=1, sticky="nsew")                  

        vbar.configure(command=self._pl_canvas.yview)

        container.rowconfigure(0, weight=1)                                   
        container.columnconfigure(1, weight=1)

        self.player_list_frame = ttk.Frame(self._pl_canvas, style="PlayerList.TFrame")         
        self._pl_window = self._pl_canvas.create_window(
            (0, 0), window=self.player_list_frame, anchor="nw"
        )                                                                
                                          
        def _sync_scrollregion(_e=None):                                      
            self._pl_canvas.configure(scrollregion=self._pl_canvas.bbox("all"))                     
            self._pl_canvas.itemconfigure(self._pl_window,                    
                                        width=self._pl_canvas.winfo_width()) 
        self.player_list_frame.bind("<Configure>", _sync_scrollregion)       
        self._pl_canvas.bind("<Configure>", _sync_scrollregion)              
                            
        self._bind_mousewheel(self._pl_canvas)                               

    def _bind_mousewheel(self, widget):                                                                                    
        widget.bind_all("<MouseWheel>", lambda e:                             
                        widget.yview_scroll(int(-1*(e.delta/120)), "units"))  
        # Linux (legacy)                                                      
        widget.bind_all("<Button-4>", lambda e: widget.yview_scroll(-3, "units"))  
        widget.bind_all("<Button-5>", lambda e: widget.yview_scroll(3, "units"))   
        # macOS                                                                
        widget.bind_all("<Shift-MouseWheel>",                                  
                        lambda e: widget.yview_scroll(int(-1*(e.delta/120)), "units"))

    def manage_players(self):
        key = self.controller.selected_team_key.get()
        roster = list(self.controller.rosters.get(key, []))
        initial = self.selected_player_var.get().strip() or None

        result = manage_players_dialog(self, players=roster, initial=initial)
        if not result:
            return
        
        action = result.get("action")
        if action == "add":
            name = result["name"]
            if name in roster:
                self.controller.set_status(f"'{name}' already on roster.")
                return
             
            self.controller.rosters[key].append(name)
            self.controller.actions.append({
                "type": "add_player",
                "team": key,
                "name": name,
                "position": "",     
                "index": len(self.controller.rosters[key]) - 1,
            })
            self.controller.redo_stack.clear()
            self.refresh_player_list()
            self._select_button_by_text(name)
            self._persist_if_saved(key)
            self.controller.set_status(f"Added {name}")

        elif action == "rename":
            old = result["old"]
            new = result["new"]
            self._rename_player(key, old, new)

        elif action == "remove":
            self._select_button_by_text(result["name"])
            self.remove_selected_player()
    
    def _persist_if_saved(self, key: str):
        try:
            tname = self.controller.team_names[key].get()
            roster = self.controller.rosters[key]
            from session_data import team_store as TS
            if TS.get_team_by_name(tname):
                TS.upsert_team(team_name=tname, roster=roster)
        except Exception:
            pass

    def _rename_player(self, key: str, old: str, new: str):
        roster = self.controller.rosters.get(key, [])
        if old not in roster:
            self.controller.set_status(f"'{old}' not found.")
            return
        if new in roster and new != old:
            self.controller.set_status(f"'{new}' already exists.")
            return

        idx = roster.index(old)
        roster[idx] = new

        roles = self.controller.player_roles.get(key, {})
        if old in roles and new not in roles: 
            roles[new] = roles.pop(old)

        for p in self.controller.data_points:
            if p.get("team") == key and p.get("player") == old:
                p["player"] = new

        self.controller.actions.append({
            "type": "rename_player",
            "team": key,
            "old": old,
            "new": new,
            "index": idx,
        })
        self.controller.redo_stack.clear()

        self.refresh_player_list()
        self._select_button_by_text(new)
        self.controller.refresh_stats()
        self._persist_if_saved(key)
        self.controller.set_status(f"Renamed player: {old} → {new}")

    
    def labels(self):
        tn = self.controller.team_names
        return {"home": tn["home"].get(), "away": tn["away"].get()}
    
    def refresh_team_dropdown(self):
        labels = self.labels()
        menu = self.team_dropdown["menu"]
        menu.delete(0, "end")

        def _add_disabled(label):
            menu.add_command(label=label, state = "disabled")

        _add_disabled("- Active Sides -")
        for key in self.controller.team_order:
            label=labels[key]
            menu.add_command(label=label, command=tk._setit(self.team_dropdown_var, label))
       
        saved = [] 
        try: 
            saved = [t.team_name for t in TS.list_teams()]
            saved = [n for n in saved if n not in labels.values()]
        except Exception:
            pass

        if saved: 
            menu.add_separator()
            _add_disabled("- Saved Teams -")
            for name in saved: 
                menu.add_command(
                    label=name, 
                    command=lambda n=name: self._apply_saved_team_to_current_side(n)
                )

        menu.add_separator()
        menu.add_command(label="Add New Team", command=self._create_new_team_via_modal)
        menu.add_command(label="Manage Teams", command=self._open_manage_teams_modal)

        current_key = self.controller.selected_team_key.get()
        self.team_dropdown_var.set(labels[current_key])

    def _apply_saved_team_to_current_side(self, saved_name: str):
        try: 
            t = TS.get_team_by_name(saved_name)
            if not t: 
                return 
            key = self.controller.selected_team_key.get()
            self.controller.team_names[key].set(t.team_name)
            self.controller.rosters[key] = list(t.roster)

            self.refresh_team_dropdown()
            self.refresh_player_list()

            if hasattr(self.controller, "refresh_stats"):
                self.controller.refresh_stats()
            self.controller.set_status(f"Applied saved team to {key.title()}: {t.team_name}")
        except Exception:
            pass 

    def _create_new_team_via_modal(self):
        try:
            result = rename_team_dialog(self, current_name="")
        except Exception: 
            result = None 
        
        if not result: 
            return 
        
        if isinstance(result, dict):
            new_name = (result.get("name") or "").strip()
            save_flag = bool(result.get("save", True))
        else:
            new_name = (str(result) or "").strip()
            save_flag = True 

        if not new_name:
            return
        
        TS.upsert_team(team_name=new_name, roster=list(DEFAULT_ROSTER))
       
        self.refresh_team_dropdown()

        if messagebox.askyesno(
            "Apply Team",
            f"Apply “{new_name}” to the current side now?",
            parent=self
        ):
            key = self.controller.selected_team_key.get()
            self.controller.team_names[key].set(new_name)
            self.controller.rosters[key] = list(DEFAULT_ROSTER)
            self.refresh_player_list()
            if hasattr(self.controller, "refresh_stats"):
                self.controller.refresh_stats()
            self.controller.set_status(f"Created & applied team “{new_name}”.")
        else:
            self.controller.set_status(f"Created team “{new_name}” (saved).")

    def _open_manage_teams_modal(self):
        try:
            saved = [t.team_name for t in TS.list_teams()]
        except Exception:
            saved = []

        from src.user_interface.modals import manage_teams_modal
        action = manage_teams_modal(self, team_names=saved)
        if not action:
            return

        kind = action.get("action")
        name = (action.get("name") or "").strip()
        if not name:
            return

        # helpers
        def _apply_to(side_key: str):
            t = TS.get_team_by_name(name)
            if not t:
                return
            self.controller.team_names[side_key].set(t.team_name)
            self.controller.rosters[side_key] = list(t.roster or [])
            self.refresh_team_dropdown()
            self.refresh_player_list()
            if hasattr(self.controller, "refresh_stats"):
                self.controller.refresh_stats()
            self.controller.set_status(f"Applied '{t.team_name}' to {side_key.title()}.")

        if kind == "apply_home":
            _apply_to("home"); return
        if kind == "apply_away":
            _apply_to("away"); return

        if kind == "delete":
            if messagebox.askyesno("Delete Team",
                                f"Delete saved team '{name}'?\n(This does not affect past games.)",
                                parent=self):
                t = TS.get_team_by_name(name)
                if t and TS.delete_team(t.team_id):
                    self.refresh_team_dropdown()
                    self.controller.set_status(f"Deleted saved team: {name}")
            return

        if kind == "rename":
            new_name = (action.get("new_name") or "").strip()
            if not new_name or new_name == name:
                return

            existing = TS.get_team_by_name(new_name)
            if existing:
                overwrite = messagebox.askyesno(
                    "Team Already Exists",
                    (f"'{new_name}' already exists. Overwrite that roster?"),
                    parent=self)
                
                if not overwrite:
                    base, n = new_name, 2
                    while TS.get_team_by_name(f"{base} ({n})"):
                        n += 1
                    new_name = f"{base} ({n})"

            t = TS.get_team_by_name(name)
            if not t:
                return
            TS.upsert_team(team_name=new_name, roster=list(t.roster or []))
            if new_name != name and existing and overwrite:
                TS.delete_team(existing.team_id)
            if name != new_name:
                old = TS.get_team_by_name(name)
                if old:
                    TS.delete_team(old.team_id)
            self.refresh_team_dropdown()
            self.controller.set_status(f"Renamed team: {name} → {new_name}")
            return

    def _delete_team_by_name(self, name: str):
        t = TS.get_team_by_name(name)
        if not t: 
            return 
        if TS.delete_team(t.team_id):
            self.refresh_team_dropdown()
            self.controller.set_status(f"Deleted saved team: {name}")


    def on_team_change(self):
        labels = self.labels()
        label = self.team_dropdown_var.get()
        key = next((k for k, v in labels.items() if v == label), "home")
        if key != self.controller.selected_team_key.get():
            self.controller.selected_team_key.set(key)
            self.refresh_player_list()
            if hasattr(self.controller, "refresh_stats"):
                self.controller.refresh_stats()

    def refresh_player_list(self):
        for w in self.player_list_frame.winfo_children():
            w.destroy()
        self.player_buttons.clear()
        self.selected_player_button = None
        self.selected_player_name = None
        self.selected_player_var.set("")      
        
        key = self.controller.selected_team_key.get()
        for role_or_name in self.controller.rosters[key]:
            b = ttk.Button(self.player_list_frame, text=role_or_name, style="Player.TButton")
            b.configure(command=lambda btn=b: self.select_player_button(btn))
            b.pack(fill="x", padx=6, pady=2)
            self.player_buttons.append(b)

        if hasattr(self, "_pl_canvas"):
            self._pl_canvas.update_idletasks()
            self._pl_canvas.configure(scrollregion=self._pl_canvas.bbox("all"))


    def set_card_colors(self, fill, border):
        self.card.configure(bg=fill, highlightbackground=border)
        style = ttk.Style(self)
        style.configure("CardInner.TFrame", background=fill)
        style.configure("PlayerList.TFrame", background=fill)
        try: 
            self._pl_canvas.configure(background=fill)
        except Exception:
            pass


    def select_player_button(self, btn: ttk.Button):
        if self.selected_player_button is btn:
            try: 
                self.selected_player_button.configure(style="Player.TButton")
            except Exception: 
                pass
            self.selected_player_button=None
            self.selected_player_name=None
            self.selected_player_var.set("")
            if hasattr(self.controller, "refresh_stats"):
                self.controller.refresh_stats()
            return

        if self.selected_player_button is not None:
            try:
                self.selected_player_button.configure(style="Player.TButton")
            except:
                pass

        btn.configure(style="PlayerSelected.TButton")
        self.selected_player_button = btn 
        self.selected_player_name = btn.cget("text")
        self.selected_player_var.set(self.selected_player_name)

        if hasattr(self.controller, "refresh_stats"):
            self.controller.refresh_stats()

    def add_player(self):
        current_key = self.controller.selected_team_key.get()
        position_choices = ["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"]
       
        res = add_player_modal(
            parent = self, 
            team_names = self.controller.team_names,
            default_team = current_key, 
            positions = position_choices,
        )
        if not res:
            return

        team_key = res["team_key"]
        player_name = res["name"]
        position = res["position"]

        self.controller.rosters[team_key].append(player_name)
        index_added = self.controller.rosters[team_key].index(player_name)
        self.controller.player_roles[team_key][player_name] = position or ""

        self.controller.actions.append({                                           
            "type": "add_player",                                                  
            "team": team_key,                                                      
            "name": player_name,                                                   
            "position": position,                                                  
            "index": index_added,                                                  
        })            
        self.controller.redo_stack.clear()       

        if team_key != current_key:
            self.controller.selected_team_key.set(team_key)
            self.refresh_team_dropdown()
        
        self.refresh_player_list()
        self._select_button_by_text(player_name)

        if hasattr(self, "selected_player_var"):                                           
            self.selected_player_var.set(player_name)

        if hasattr(self.controller, "set_status"):
            team_label = self.controller.team_names[team_key].get()
            self.controller.set_status(f"Added {player_name} ({position}) to {team_label}")
            
        try: 
            team_key = self.controller.selected_team_key.get()
            tname = self.controller.team_names[team_key].get()
            roster = self.controller.rosters[team_key]
            if TS.get_team_by_name(tname):
                TS.upsert_team(team_name = tname, roster = roster)
        except Exception: 
            pass

    def _select_button_by_text(self, text: str):
        for btn in self.player_buttons: 
            if btn.cget("text") == text: 
                self.select_player_button(btn)
                break

    def remove_selected_player(self):
        if not self.selected_player_button:
            return
        name = self.selected_player_button.cget("text")
        key = self.controller.selected_team_key.get()
        team_label = self.controller.team_names[key].get()

        affected_shots = [
            p for p in self.controller.data_points                  
            if p.get("team") == key and p.get("player") == name]  

        if affected_shots:                                                            
            if not confirm(
                "shots_assigned", self,
                name=name, team=team_label,
                count=len(affected_shots)
                ):
                return
            if not confirm("confirm_remove_player", self, name=name, team=team_label):
                        return  
        else: 
            if not confirm("confirm_remove_player", self, name=name, team=team_label):
                return 
            
        try: 
            idx = self.controller.rosters[key].index(name)
        except ValueError:
            idx = None

        if affected_shots:
            for p in affected_shots: 
                p["player"] = "Unassigned"

        try:
            self.controller.rosters[key].remove(name)
        except ValueError:
            pass
        
        self.controller.actions.append({                                           
            "type": "remove_player",                                               
            "team": key,                                                           
            "name": name,                                                          
            "index": idx,
            "shot_refs": affected_shots,                                                          
        })                                                        
        self.controller.redo_stack.clear()                                      
    
        try: 
            self.controller.player_roles[key].pop(name, None)
        except Exception:
            pass

        self.selected_player_button = None
        self.refresh_player_list()
        self.selected_player_var.set("")
        self.controller.refresh_stats()
    

        try: 
            tname = self.controller.team_names[key].get()
            roster = self.controller.rosters[key]
            if TS.get_team_by_name(tname):
                TS.upsert_team(team_name = tname, roster = roster)
        except Exception:
            pass

        if affected_shots:
            self.controller.set_status(
                f"Removed {name} — {len(affected_shots)} shots set to 'Unassigned'"
            )
        else:
            self.controller.set_status(f"Removed {name} from {team_label}")

                
    def get_selected_player_name(self) -> str | None: 
        try: 
            name = self.selected_player_var.get().strip()
            return name or None 
        except Exception: 
            return None 


class StatusBar(ttk.Frame): 
    def __init__(self, parent): 
        super().__init__(parent)

        self.grid_propagate(False)
        self.configure(height = BAR_HEIGHT - 8)

        self.grid_columnconfigure(0, weight = 1)
        
        self.message_variable = tk.StringVar(value = "Ready.")
        ttk.Label(self, textvariable=self.message_variable).grid(
            row = 0, column = 0, padx = 10, pady = 6, sticky = "ew")

    def set_status(self, text: str):
        self.message_variable.set(text)

                         
class DataBar(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.grid_propagate(False)
        self.configure(width=SIDE_WIDTH)

        self.grid_columnconfigure(0, weight=1)

        ttk.Label(self, text="Stats", anchor="center").grid(
            row=0, column=0, sticky="ew", padx=8, pady=(10,6)
        )
        self.home_section = self._make_team_section(self, team_key="home", row=1)
        self.away_section = self._make_team_section(self, team_key="away", row=2)
        self.player_section = self._make_player_section(self, row = 3)

        for key, name_var in self.controller.team_names.items():
            name_var.trace_add("write", lambda *_, k=key: self._sync_heading(k))
        
        self._sync_heading("home")
        self._sync_heading("away")

        self.refresh_from_points(self.controller.data_points)

    def _make_team_section(self, parent, team_key: str, row: int):
        box = ttk.LabelFrame(parent, text="", padding = 8)
        box.grid(row=row, column=0, sticky="nsew", padx=8, pady=(0,8))
        box.grid_columnconfigure(1, weight=1)

        vars = { 
            "shots": tk.IntVar(value=0),
            "made": tk.IntVar(value=0),
            "missed": tk.IntVar(value=0),
            "accuracy_fg": tk.StringVar(value="-"),
            "avg_made_ft": tk.StringVar(value="-"),
            "avg_missed_ft": tk.StringVar(value="-"),
            "heading": tk.StringVar(value="-"),
            "dom_zone": tk.StringVar(value="-"),
            "weak_zone": tk.StringVar(value="-"),   
        }

        box.configure(labelwidget=ttk.Label(box, textvariable=vars["heading"]))

        r=0
        ttk.Label(box, text="Shots Taken:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["shots"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="Shots Made:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["made"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="Shots Missed:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["missed"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="Accuracy:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["accuracy_fg"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="Average Made Distance:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["avg_made_ft"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="Average Missed Distance:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["avg_missed_ft"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="Dominant Zone:").grid(row=r, column=0, sticky="w");ttk.Label(box, textvariable=vars["dom_zone"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="Weak Zone:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["weak_zone"]).grid(row=r, column=1, sticky="e"); r += 1 


        if not hasattr(self, "_team_vars"):
            self._team_vars = {}
        self._team_vars[team_key] = vars
        return box
    
    def _sync_heading(self, team_key: str):
        team_name = self.controller.team_names.get(team_key, tk.StringVar(value=team_key.title())).get()
        self._team_vars[team_key]["heading"].set(f"{team_name} Stats")

    def refresh_from_points(self, points: list[dict]):
        stats = {
            "home": {"shots": 0, "made": 0, "missed": 0, "made_dists": [], "miss_dists": []},
            "away": {"shots": 0, "made": 0, "missed": 0, "made_dists": [], "miss_dists": []},
        }

        for p in points or []:
            team = p.get("team")
            if team not in stats: 
                continue

            s = stats[team]
            s["shots"] += 1
            if p.get("made"):
                s["made"] += 1
                if "r_ft" in p: 
                    s["made_dists"].append(p["r_ft"])
            else: 
                s["missed"] += 1
                if "r_ft" in p: 
                    s["miss_dists"].append(p["r_ft"])
        
        player_name = None
        team_key_sel = None

        if hasattr(self.controller, "get_selected_player"):
            player_name = self.controller.get_selected_player()

        if hasattr(self.controller, "selected_team_key"):
            try:
                team_key_sel = self.controller.selected_team_key.get()
            except Exception:
                team_key_sel = None

        def fmt_avg(lst):
            if lst: 
                return f"{(sum(lst) / len(lst)):.1f} ft" 
            return "-"
    
        if not player_name: 
            pv = self._player_vars
            pv["heading"].set("Selected Player:")
            pv["shots"].set(0); pv["made"].set(0); pv["missed"].set(0)
            pv["accuracy_fg"].set("-"); pv["avg_made_ft"].set("-"); pv["avg_missed_ft"].set("-")
            pv["dom_zone"].set("-"); pv["weak_zone"].set("-")
        else: 
            pshots = [p for p in (points or [])
                  if p.get("player") == player_name and p.get("team") == team_key_sel]

            shots  = len(pshots)
            made   = sum(1 for p in pshots if p.get("made"))
            missed = shots - made
            made_d   = [p.get("r_ft") for p in pshots if p.get("made") and isinstance(p.get("r_ft"), (int, float))]
            missed_d = [p.get("r_ft") for p in pshots if not p.get("made") and isinstance(p.get("r_ft"), (int, float))]
            fg = f"{(made / shots * 100):.1f}%" if shots else "-"

            team_label = self.controller.team_names.get(team_key_sel, tk.StringVar(value=team_key_sel.title())).get()
            dom, weak = self._zone_strength(pshots)

            pv = self._player_vars
            pv["heading"].set(f"{player_name} ({team_label})")
            pv["shots"].set(shots)
            pv["made"].set(made)
            pv["missed"].set(missed)
            pv["accuracy_fg"].set(fg)
            pv["avg_made_ft"].set(fmt_avg(made_d))
            pv["avg_missed_ft"].set(fmt_avg(missed_d))
            pv["dom_zone"].set(short_zone(dom))
            pv["weak_zone"].set(short_zone(weak))

        for team_key in ("home", "away"): 
            s = stats[team_key]
            shots = s["shots"]
            made = s["made"]
            missed = s["missed"]
            pct = f"{(made / shots * 100):.1f}%" if shots else "-"
                
            team_shots = [p for p in (points or []) if p.get("team") == team_key]
            dom, weak = self._zone_strength(team_shots)

            vars = self._team_vars[team_key]
            vars["shots"].set(shots)
            vars["made"].set(made)
            vars["missed"].set(missed)
            vars["accuracy_fg"].set(pct)
            vars["avg_made_ft"].set(fmt_avg(s["made_dists"]))
            vars["avg_missed_ft"].set(fmt_avg(s["miss_dists"]))
            vars["dom_zone"].set(short_zone(dom))
            vars["weak_zone"].set(short_zone(weak))

        def _is_three_by_zone(z: str) -> bool:
            z = (z or "").lower()
            return any(tok in z for tok in ("3pt", "3-pt", "three", "corner 3", "wing 3", "top 3", "3 point", "3-pointer"))

        def _points_for(p: dict) -> int:
            if not p.get("made"):
                return 0
            st = (p.get("shot_type") or "").strip().lower()
            if st == "free throw" or p.get("ft_reason"):  
                return 1
            if _is_three_by_zone(p.get("zone")):
                return 3
            try:
                if float(p.get("r_ft", 0)) >= 22.0:
                    return 3
            except Exception:
                pass
            return 2

        home_pts = sum(_points_for(p) for p in (points or []) if p.get("team") == "home")
        away_pts = sum(_points_for(p) for p in (points or []) if p.get("team") == "away")

        if hasattr(self.controller, "home_score"):
            try:
                self.controller.home_score.set(int(home_pts))
            except Exception:
                self.controller.home_score.set(0)

        if hasattr(self.controller, "away_score"):
            try:
                self.controller.away_score.set(int(away_pts))
            except Exception:
                self.controller.away_score.set(0)

    def _make_player_section(self, parent, row: int):
        box = ttk.LabelFrame(parent, text="", padding=8)
        box.grid(row = row, column = 0, sticky = "nsew", padx = 8, pady = (0,8))
        box.grid_columnconfigure(1, weight = 1)

        vars = {
            "heading": tk.StringVar(value="Selected Player: _"), 
            "shots": tk.IntVar(value=0), 
            "made": tk.IntVar(value=0),
            "missed": tk.IntVar(value=0),
            "accuracy_fg": tk.StringVar(value="-"),
            "avg_made_ft": tk.StringVar(value="-"),
            "avg_missed_ft": tk.StringVar(value="-"),
            "dom_zone": tk.StringVar(value="-"),
            "weak_zone": tk.StringVar(value="-")
        }
        box.configure(labelwidget=ttk.Label(box, textvariable=vars["heading"]))

        r=0
        ttk.Label(box, text="Shots Taken:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["shots"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="Shots Made:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["made"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="Shots Missed:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["missed"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="Accuracy:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["accuracy_fg"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="Average Made Distance:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["avg_made_ft"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="Average Missed Distance:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["avg_missed_ft"]).grid(row=r, column=1, sticky="e"); r+=1
        ttk.Label(box, text="Dominant Zone:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["dom_zone"]).grid(row=r, column=1, sticky="e"); r += 1
        ttk.Label(box, text="Weak Zone:").grid(row=r, column=0, sticky="w"); ttk.Label(box, textvariable=vars["weak_zone"]).grid(row=r, column=1, sticky="e"); r += 1
        
        self._player_vars = vars 
        return box 

    def _points_for(self, p:dict) -> int:
        if not p.get("made"):
            return 0
        
        st = (p.get("shot_type") or "").strip().lower()
        if st == "free throw": 
            return 1
        
        z = (p.get("zone") or "").strip().lower()
        if "3pt" in z or "three" in z or "3" in z: 
            return 3
        
        return 2

    def _zone_strength(self, shots: list[dict]) -> tuple[str, str]:
        per = {}
        for p in shots:
            z = p.get("zone")
            if not z:
                continue
            d = per.setdefault(z, {"made": 0, "att": 0})
            d["att"] += 1
            if p.get("made"):
                d["made"] += 1
        if not per:
            return "-", "-"

        items = [(z, v["made"], v["att"]) for z, v in per.items() if v["att"] > 0]
        if not items:
            return "-", "-"

        dom = max(items, key=lambda t: (t[1], t[1] / t[2], t[2], t[0]))[0]   
        weak = min(items, key=lambda t: (t[1], t[1] / t[2], -t[2], t[0]))[0]

        return dom, weak