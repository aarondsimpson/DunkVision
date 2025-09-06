import json 
import csv
import tkinter as tk
import os 
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from pathlib import Path

from src.user_interface.court_canvas import ScreenImage
from src.user_interface.player_dialogs import confirm, info, error, resolve
from src.user_interface.modals import add_player_dialog as add_player_modal, rename_team_dialog, shot_result_dialog, dunk_or_layup_dialog
from src.application_logic.zoning import resolve_zone
from src.application_logic.zoning_configuration import shot_distance_from_hoop 
from src import config

BAR_HEIGHT = 60
SIDE_WIDTH = 300

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

class CourtFrame(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller= controller or self
        self.game_date = None
        self.game_location = None
        
        #State Definition 
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
            "home": ["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"],
            "away": ["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"],
        }
        self.selected_team_key=tk.StringVar(value="home")

        #Layout Scaffold
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=SIDE_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        #Widget Scaffold
        self.topbar=TopBar(
            self, 
            on_toggle_mode=self.toggle_mode,
            on_home_button=self.home_button,
            on_undo_action=self.undo_action,
            on_redo_action=self.redo_action,
            on_select_quarter=self.select_quarter,
            on_save_game=self.save_game,
            on_reset_game=self.reset_game,
            on_end_game=self.end_game, 
            on_export_image=self.export_image,
            on_export_csv=self.export_csv,
            on_export_json=self.export_json,
            quarter_var=self.quarter, 
            )
        self.topbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0,4))

        self.sidebar=SideBar(self, controller=self)
        self.sidebar.grid(row=1, column=0, sticky="nsew")

        self.center_canvas=ScreenImage(self)
        self.center_canvas.grid(row=1, column=1, sticky="nsew")

        c = self.center_canvas.canvas
        self._shot_markers: list[dict] = []
        
        c.bind("<Button-1>", self._on_canvas_click, add="+")
        def _reposition_after_render(_evt=None):
            self.after_idle(self._reposition_markers)
        c.bind("<Configure>", lambda e: self.after_idle(self._reposition_markers), add="+")

        from src.application_logic.zoning_configuration import MASK
        print("COURT_ART source size:", self.center_canvas.images["court_dark"].size)
        print("MASK size:", MASK.img.size)
        
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
        
    def undo_action(self):
        if not self.actions:
            self.set_status("Nothing to Undo.")
            return
        
        action=self.actions.pop()
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
                # also drop from our marker registry
                self._shot_markers = [m for m in self._shot_markers if m.get("id") != mid]

            self.refresh_stats()
            self.set_status("Undid: shot")
            # make sure remaining dots stay on top
            self.center_canvas.canvas.tag_raise("shot_marker")
        else:
            self.set_status(f"Undid: {action.get('type','action')}")
        
    def redo_action(self):
        if not self.redo_stack:
            self.set_status("Nothing to Redo.")
            return

        action = self.redo_stack.pop()
        self.actions.append(action)

        if action.get("type") == "shot":
            # 1) re-add datapoint without creating a new 'action'
            point = action.get("data")
            self.data_points.append(point)

            # 2) recreate the canvas marker from saved meta
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
        else:
            self.set_status(f"Redid: {action.get('type','action')}")

    def select_quarter(self, q:str):
        self.quarter.set(q)
        self.set_status(f"Quarter: {q}")
                
    def save_game(self):
        self.set_status("Save game (stub).") #Requires build out when saving persistence format is built

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
                   
    def end_game(self):
        self.set_status("End game (stub).") #Build confirmation dialog

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
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data_points, f, ensure_ascii=False, indent=2)
        self.set_status(f"JSON Exported: {path}")

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Export Data (CSV)",
        )
        if not path:
            return
        rows = self.data_points
        if not rows: 
            with open(path, "w", newline="", encoding="utf-8") as f:
                f.write("")
            self.set_status(f"CSV Exported (Empty): {path}")
            return
        fieldnames = sorted({k for row in rows for k in row.keys()})
        with open(path, "w", newline="",encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        self.set_status(f"CSV Exported: {path}")

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
        self.team_names[team_key].set(new_name)
        if hasattr(self.sidebar, "refresh_team_dropdown"):
            self.sidebar.refresh_team_dropdown()
        self.set_status(f"Team Renamed: {current} -> {new_name}")

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

        if kind_norm == "no_click": 
            self.set_status(f"{label} - not a playable zone.")
            return 
        if kind_norm in ("out_of_bounds", "unknown"):
            self.set_status(label)
            return 
        
       
        player_name = self.sidebar.get_selected_player_name()
        if not player_name:
            self.set_status("Select a player first.")
            return 
        
        r_ft, dx_ft, dy_ft = shot_distance_from_hoop(ix, iy)

        res = shot_result_dialog(self)
        if res is None: 
            return
        made = bool(res)

        is_dunk_zone = (
            kind_norm == "dunk_zone" or
            "dunk" in (label or "").lower()
        )
        shot_kind = None
        if is_dunk_zone:
            shot_kind = dunk_or_layup_dialog(self)
            if shot_kind is None: 
                return

        team_key = self.selected_team_key.get()        
        marker = self._draw_marker(ix, iy, made=made, team=team_key)

        team_name = self.team_names[team_key].get()
        kind_suffix = f" - {shot_kind}" if shot_kind else ""
        status_text = (
            f"{team_name}: {player_name} - {label}{kind_suffix} - "
            f"{r_ft:.1f} ft (Q{self.quarter.get()[-1]})"
        )

        meta = {"player": player_name, "zone": label,
                "r_ft": r_ft, "dx_ft": dx_ft, "dy_ft": dy_ft}
        if shot_kind: 
            meta["shot_type"] = shot_kind

        self.record_shot(
            team=team_key, 
            x=ix, y=iy, 
            made=made, airball=False,
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
            on_select_quarter=None, on_end_game=None,
            on_save_game=None, on_reset_game=None,  
            on_export_image=None, on_export_json=None, on_export_csv=None,
            quarter_var: tk.StringVar | None=None,
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
        mid.grid(row=0, column=1, sticky = "n", pady=6)

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

        end_button_column = base_column + len(quarters)
        ttk.Button(mid, text="End Game", command=on_end_game or (lambda:None)
                   ).grid(row=0, column = end_button_column, padx=(12,3))


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

        #Team Selector
        self.team_dropdown_var = tk.StringVar()
        self.team_dropdown = ttk.OptionMenu(self.inner, self.team_dropdown_var, "")
        self.team_dropdown.grid(row=1, column=0, sticky="ew", padx=8)
        
        #Player List Container
        self.player_list_frame = ttk.Frame(self.inner, style="PlayerList.TFrame")
        self.player_list_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=(8,10))
        self.inner.rowconfigure(2, weight=1)
        self.inner.columnconfigure(0, weight=1)

        #Add and Remove Buttons
        self.add_btn = ttk.Button(self.inner, text="Add Player", command=self.add_player)
        self.add_btn.grid(row = 3, column = 0, padx = 8, pady = (6,4), sticky = "ew")

        self.remove_btn = ttk.Button(self.inner, text = "Remove Player", command=self.remove_selected_player, state = "disabled")
        self.remove_btn.grid(row = 4, column = 0, padx = 8, pady = (0,8), sticky = "ew")

        ttk.Separator(self.inner, orient = "horizontal").grid(row = 5, column = 0, padx = 8, pady= (0,6), sticky = "ew")

        self.rename_btn = ttk.Button(self.inner, text = "Rename Team", command=self.rename_team)
        self.rename_btn.grid(row = 6, column = 0, padx = 9, pady = (0,10), sticky = "ew")

        self.player_buttons = []
        self.selected_player_button = None #track selection
        self.selected_player_name = None
        self.selected_player_var = tk.StringVar(value="")
        self.selected_player_var.trace_add("write", lambda *_: (
            hasattr(self.controller, "refresh_stats") and self.controller.refresh_stats()
        ))

        self.refresh_team_dropdown()
        self.team_dropdown_var.trace_add("write", lambda *_: self.on_team_change())
        self.refresh_player_list()
        
    #Helper Functions 

    def labels(self):
        tn = self.controller.team_names
        return {"home": tn["home"].get(), "away": tn["away"].get()}
    
    def refresh_team_dropdown(self):
        labels = self.labels()
        menu = self.team_dropdown["menu"]
        menu.delete(0, "end")
        for key in self.controller.team_order:
            label=labels[key]
            menu.add_command(label=label, command=tk._setit(self.team_dropdown_var, label))
        current_key = self.controller.selected_team_key.get()
        self.team_dropdown_var.set(labels[current_key])

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
        self.remove_btn.configure(state="disabled")

        key = self.controller.selected_team_key.get()
        for role_or_name in self.controller.rosters[key]:
            b = ttk.Button(self.player_list_frame, text=role_or_name, style="Player.TButton")
            b.configure(command=lambda btn=b: self.select_player_button(btn))
            b.pack(fill="x", padx=6, pady=2)
            self.player_buttons.append(b)

    def set_card_colors(self, fill, border):
        self.card.configure(bg=fill, highlightbackground=border)
        style = ttk.Style(self)
        style.configure("CardInner.TFrame", background=fill)
        style.configure("PlayerList.TFrame", background=fill)

    #Button Handlers 
    
    def select_player_button(self, btn: ttk.Button):
        if self.selected_player_button is btn:
            try: 
                self.selected_player_button.configure(style="Player.TButton")
            except Exception: 
                pass
            self.selected_player_button=None
            self.selected_player_name=None
            self.selected_player_var.set("")
            self.remove_btn.configure(state="disabled")
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
        self.remove_btn.configure(state="normal")

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

        if team_key != current_key:
            self.controller.selected_team_key.set(team_key)
            self.refresh_team_dropdown()
        
        self.refresh_player_list()
        self._select_button_by_text(player_name)

        if hasattr(self.controller, "set_status"):
            team_label = self.controller.team_names[team_key].get()
            self.controller.set_status(f"Added {player_name} ({position}) to {team_label}")
            
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
        if not confirm("confirm_remove_player", self, name=name, team=team_label):
            return
        try:
            self.controller.rosters[key].remove(name)
        except ValueError:
            pass
        self.selected_player_button=None
        if hasattr(self, "remove_btn"):
            self.remove_btn.configure(state="disabled")
        self.refresh_player_list()
  
    def rename_team(self):
        labels=self.labels()
        current_label=self.team_dropdown_var.get()
        team_key=next((k for k, v in labels.items() if v == current_label), "home")
        if hasattr(self.controller, "rename_team"):
            self.controller.rename_team(team_key)
        self.refresh_team_dropdown()
                
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

        vars = { #Add more as development continues
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
        ttk.Label(box, text="Dominant Zone").grid(row=r, column=0, sticky="w");ttk.Label(box, textvariable=vars["dom_zone"]).grid(row=r, column=1, sticky="e"); r+=1
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
            pv["dom_zone"].set(dom); pv["weak_zone"].set(weak)

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
            vars["dom_zone"].set(dom)
            vars["weak_zone"].set(weak)

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

