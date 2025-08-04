import pyautogui
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from PIL import Image
import numpy as np
import pandas as pd
import tkinter as tk
import cv2
import time
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             
# CONFIGURATION
BOARD_REGION = None  # (left, top, width, height)
TILE_SIZE = 50  # Approximate size in pixels
TILE_ROWS = 5
TILE_COLS = 5
MINE_COUNT = 3
heatmap = None
total_games = 0

# Initialize Tesseract
pytesseract.pytesseract.tesseract_cmd = 'tesseract'  # Change if not in PATH

def capture_board(region):
    screenshot = pyautogui.screenshot(region=region)
    return screenshot

def detect_tiles(image):
    # Convert to OpenCV format
    cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    tiles = []
    for row in range(TILE_ROWS):
        tile_row = []
        for col in range(TILE_COLS):
            x = col * TILE_SIZE
            y = row * TILE_SIZE
            tile_img = cv_img[y:y+TILE_SIZE, x:x+TILE_SIZE]
            # Safeguard: skip empty tiles
            if tile_img.shape[0] == 0 or tile_img.shape[1] == 0:
                tile_row.append(None)
            else:
                tile_row.append(tile_img)
        tiles.append(tile_row)
    return tiles

def color_distance(c1, c2):
    return np.sqrt(np.sum((np.array(c1) - np.array(c2)) ** 2))

def classify_tile(tile_img, color_refs):
    # tile_img: OpenCV image (BGR) or None
    if tile_img is None or tile_img.shape[0] == 0 or tile_img.shape[1] == 0:
        return 'unknown'
    # Convert to RGB and take center pixel
    h, w, _ = tile_img.shape
    center_pixel = tile_img[h//2, w//2][::-1]  # BGR to RGB
    dists = {k: color_distance(center_pixel, v) for k, v in color_refs.items()}
    min_type = min(dists, key=dists.get)
    if dists[min_type] < 60:  # threshold
        return min_type
    return 'unknown'

import os
import pickle

def update_heatmap(tile_results):
    global heatmap, total_games
    for row in range(TILE_ROWS):
        for col in range(TILE_COLS):
            if tile_results[row][col] == 'mine':
                heatmap[row][col] += 1
    total_games += 1
    save_heatmap()

def save_heatmap():
    with open('heatmap.pkl', 'wb') as f:
        pickle.dump({'heatmap': heatmap, 'total_games': total_games}, f)

def load_heatmap():
    global heatmap, total_games
    if os.path.exists('heatmap.pkl'):
        with open('heatmap.pkl', 'rb') as f:
            data = pickle.load(f)
            heatmap = data['heatmap']
            total_games = data.get('total_games', 0)

def suggest_safe_tiles():
    # Suggest tiles with the lowest mine frequency
    min_val = np.min(heatmap)
    safe_tiles = np.argwhere(heatmap == min_val)
    return safe_tiles

import random

def predict_bomb_locations():
    # Predict bomb locations based on the highest heatmap values
    flat_heatmap = heatmap.flatten()
    sorted_indices = np.argsort(flat_heatmap)[::-1]  # descending order
    bomb_candidates = []
    last_val = None
    for idx in sorted_indices:
        val = flat_heatmap[idx]
        if len(bomb_candidates) < MINE_COUNT:
            bomb_candidates.append(idx)
            last_val = val
        elif val == last_val:
            bomb_candidates.append(idx)
        else:
            break
    # If more candidates than needed, randomly choose
    chosen = random.sample(bomb_candidates, MINE_COUNT)
    coords = [divmod(idx, TILE_COLS) for idx in chosen]
    return set(coords)

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class PredictorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dubibet Mines Predictor")
        self.geometry(f"760x700")
        self.resizable(False, False)
        self.running = False
        self.after_id = None

        self.setup_config_ui()

    def setup_config_ui(self):
        self.config_frame = ctk.CTkFrame(self, fg_color=("#23272e", "#23272e"), corner_radius=16)
        self.config_frame.pack(fill='both', expand=True, padx=32, pady=24)

        # Modern header
        ctk.CTkLabel(self.config_frame, text="Dubibet Mines Predictor", font=("Segoe UI", 24, "bold"), text_color="#00cfff").pack(pady=(0, 8))
        ctk.CTkLabel(self.config_frame, text="Setup & Configuration", font=("Segoe UI", 15), text_color="#bbbbbb").pack(pady=(0, 18))

        self.rows_var = ctk.IntVar(value=5)
        self.cols_var = ctk.IntVar(value=5)
        self.mines_var = ctk.IntVar(value=3)

        entry_frame = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        entry_frame.pack(pady=(0, 16))
        # Board Rows
        ctk.CTkLabel(entry_frame, text="Rows:", font=("Segoe UI", 13)).grid(row=0, column=0, sticky='e', padx=(0, 6), pady=6)
        ctk.CTkEntry(entry_frame, textvariable=self.rows_var, width=40, font=("Segoe UI", 13), corner_radius=8).grid(row=0, column=1, pady=6)
        # Board Columns
        ctk.CTkLabel(entry_frame, text="Columns:", font=("Segoe UI", 13)).grid(row=1, column=0, sticky='e', padx=(0, 6), pady=6)
        ctk.CTkEntry(entry_frame, textvariable=self.cols_var, width=40, font=("Segoe UI", 13), corner_radius=8).grid(row=1, column=1, pady=6)
        # Mine Count
        ctk.CTkLabel(entry_frame, text="Mines:", font=("Segoe UI", 13)).grid(row=2, column=0, sticky='e', padx=(0, 6), pady=6)
        ctk.CTkEntry(entry_frame, textvariable=self.mines_var, width=40, font=("Segoe UI", 13), corner_radius=8).grid(row=2, column=1, pady=6)

        self.region_label = ctk.CTkLabel(self.config_frame, text="Board Region: Not Set", font=("Segoe UI", 12, "bold"), text_color="#ffb347")
        self.region_label.pack(pady=8)
        ctk.CTkButton(self.config_frame, text="Select Board Region", command=self.select_region, fg_color="#00cfff", hover_color="#007fa3", text_color="#23272e", font=("Segoe UI", 13, "bold"), corner_radius=10).pack(pady=(0,14))

        # Color pickers (optional: could be modernized further)
        self.color_refs = {'unclicked': (200,200,200), 'gem': (0,255,0), 'mine': (255,0,0)}
        tk.Label(self.config_frame, text="Pick tile colors (click to sample)").pack(pady=5)
        self.color_labels = {}
        for t in ['unclicked','gem','mine']:
            btn = tk.Button(self.config_frame, text=f"Pick {t} color", command=lambda tt=t: self.pick_color(tt))
            btn.pack()
            lbl = tk.Label(self.config_frame, text=f"{t.title()} color: {self.color_refs[t]}")
            lbl.pack()
            self.color_labels[t] = lbl
        ctk.CTkButton(self.config_frame, text="🚀 Start Predictor", command=self.launch_predictor, fg_color="#00cfff", hover_color="#007fa3", text_color="#23272e", font=("Segoe UI", 15, "bold"), corner_radius=12, height=45, width=220).pack(pady=18)

    def pick_color(self, tile_type):
        import pyautogui
        self.withdraw()
        tk.messagebox.showinfo("Pick Color", f"Move your mouse to a {tile_type} tile and press OK.")
        x, y = pyautogui.position()
        rgb = pyautogui.screenshot().getpixel((x, y))
        self.color_refs[tile_type] = rgb
        self.color_labels[tile_type].config(text=f"{tile_type.title()} color: {rgb}")
        self.deiconify()

    def select_region(self):
        self.withdraw()
        self.after(500, self._region_select_popup)

    def _region_select_popup(self):
        import pyautogui
        import tkinter.simpledialog
        tk.messagebox.showinfo(
            "Region Selection",
            "Step 1: Move your mouse to the TOP-LEFT corner of the game board and press OK.\n\nTip: Make sure the region is fully visible on your screen."
        )
        x1, y1 = pyautogui.position()
        tk.messagebox.showinfo(
            "Region Selection",
            "Step 2: Move your mouse to the BOTTOM-RIGHT corner of the game board and press OK.\n\nTip: The region should cover the entire board and be within your screen bounds."
        )
        x2, y2 = pyautogui.position()
        global BOARD_REGION
        # Ensure width and height are positive
        width = max(1, x2 - x1)
        height = max(1, y2 - y1)
        BOARD_REGION = (x1, y1, width, height)
        # Warn if region is not divisible by grid
        if width % TILE_COLS != 0 or height % TILE_ROWS != 0:
            tk.messagebox.showwarning(
                "Region/Grid Mismatch",
                f"Warning: The selected region size ({width}x{height}) is not evenly divisible by the board size ({TILE_COLS}x{TILE_ROWS}).\nSome tiles may be empty."
            )
        if hasattr(self, 'region_label') and self.region_label.winfo_exists():
            self.region_label.configure(text=f"Board Region: {BOARD_REGION}", text_color="green")
        self.deiconify()

    def launch_predictor(self):
        global TILE_ROWS, TILE_COLS, MINE_COUNT, heatmap
        TILE_ROWS = self.rows_var.get()
        TILE_COLS = self.cols_var.get()
        MINE_COUNT = self.mines_var.get()
        heatmap = np.zeros((TILE_ROWS, TILE_COLS), dtype=int)
        self.config_frame.destroy()
        self.setup_predictor_ui()

    def detect_platform(self):
        import pyautogui, pytesseract
        # Screenshot the entire screen (or region if you want to optimize)
        screenshot = pyautogui.screenshot()
        text = pytesseract.image_to_string(screenshot).lower()
        if "stake" in text:
            return "Stake"
        elif "dubibet" in text:
            return "Dubibet"
        else:
            return "Unknown"

    def setup_predictor_ui(self):
        # Modern geometry and background
        self.geometry(f"{TILE_COLS*TILE_SIZE+260}x{TILE_ROWS*TILE_SIZE+160}")
        board_frame = ctk.CTkFrame(self, fg_color="#181a20", corner_radius=18, width=TILE_COLS*TILE_SIZE, height=TILE_ROWS*TILE_SIZE)
        board_frame.place(x=28, y=90)
        self.canvas = tk.Canvas(board_frame, width=TILE_COLS*TILE_SIZE, height=TILE_ROWS*TILE_SIZE, bg="#181a20", highlightthickness=0, bd=0)
        self.canvas.pack()

        # Detect platform and store
        self.platform = self.detect_platform()

        # Status and info labels
        self.status_label = ctk.CTkLabel(self, text=f"Status: Ready | Platform: {self.platform}", anchor='w', font=("Segoe UI", 13, "bold"), text_color="#ffb347")
        self.status_label.place(x=36, y=30)
        self.info_label = ctk.CTkLabel(self, text=f"Board: {TILE_ROWS}x{TILE_COLS} | Mines: {MINE_COUNT}", anchor='w', font=("Segoe UI", 12), text_color="#bbbbbb")
        self.info_label.place(x=36, y=60)

        # Modern buttons
        self.start_btn = ctk.CTkButton(self, text="▶ Start", command=self.start_predictor, fg_color="#00cfff", hover_color="#007fa3", text_color="#23272e", font=("Segoe UI", 13, "bold"), corner_radius=10, width=120, height=44)
        self.start_btn.place(x=TILE_COLS*TILE_SIZE+70, y=130)
        self.pause_btn = ctk.CTkButton(self, text="⏸ Pause", command=self.pause_predictor, fg_color="#393e46", hover_color="#23272e", text_color="#f2f2f2", font=("Segoe UI", 13, "bold"), corner_radius=10, width=120, height=44)
        self.pause_btn.place(x=TILE_COLS*TILE_SIZE+70, y=190)
        self.log_btn = ctk.CTkButton(self, text="📝 Log Round", command=self.log_round, fg_color="#23272e", hover_color="#00cfff", text_color="#00cfff", font=("Segoe UI", 13, "bold"), corner_radius=10, border_width=2, border_color="#00cfff", width=120, height=44)
        self.log_btn.place(x=TILE_COLS*TILE_SIZE+70, y=250)
        self.current_tile_results = None

    def draw_board(self, bomb_tiles, tile_results=None):
        import math
        self.canvas.delete('all')
        pulse_phase = math.sin(time.time() * 2) * 0.5 + 0.5  # for pulsing effect
        for row in range(TILE_ROWS):
            for col in range(TILE_COLS):
                x1, y1 = col*TILE_SIZE, row*TILE_SIZE
                x2, y2 = x1+TILE_SIZE, y1+TILE_SIZE
                cx, cy = (x1+x2)//2, (y1+y2)//2
                # Determine fill based on tile type
                tile_type = None
                if tile_results:
                    tile_type = tile_results[row][col]
                # Gradient fill for modern look
                if tile_type == 'gem':
                    fill = '#00ffd0'
                elif tile_type == 'mine':
                    fill = '#ff0040'
                elif tile_type == 'unclicked':
                    fill = '#3a3d4d'
                else:
                    fill = '#23272e'
                # Modern rounded rectangle with shadow
                shadow_offset = 4
                self.canvas.create_oval(x1+shadow_offset, y1+shadow_offset, x2+shadow_offset, y2+shadow_offset, fill='#181a20', outline='', width=0)
                # Bomb highlight: pulsing neon glow
                if (row, col) in bomb_tiles:
                    glow_color = f"#ff00{hex(int(128+127*pulse_phase))[2:]:>02}"
                    self.canvas.create_oval(x1-7, y1-7, x2+7, y2+7, fill=glow_color, outline='', width=0)
                    outline = '#ff00ff'
                else:
                    outline = '#444'
                # Draw main tile
                self.canvas.create_oval(x1, y1, x2, y2, fill=fill, outline=outline, width=4)
                # Draw a symbol for gem/mine
                if tile_type == 'gem':
                    self.canvas.create_text(cx, cy, text='💎', font=('Segoe UI Emoji', 24))
                elif tile_type == 'mine':
                    self.canvas.create_text(cx, cy, text='💣', font=('Segoe UI Emoji', 24))
        self.info_label.configure(text=f"Board: {TILE_ROWS}x{TILE_COLS} | Mines: {MINE_COUNT}")

    def start_predictor(self):
        global BOARD_REGION
        if BOARD_REGION is None or not isinstance(BOARD_REGION, tuple) or len(BOARD_REGION) != 4 or any(v <= 0 for v in BOARD_REGION[2:]):
            tk.messagebox.showwarning("Board Region Required", "Please select a valid board region before starting the predictor.")
            self.select_region()
            return
        self.running = True
        self.status_label.configure(text="Status: Running")
        self.run_prediction_loop()

    def pause_predictor(self):
        self.running = False
        self.status_label.configure(text="Status: Paused")
        if self.after_id:
            self.after_cancel(self.after_id)

    def run_prediction_loop(self):
        global BOARD_REGION
        if not self.running:
            return
        if BOARD_REGION is None or not isinstance(BOARD_REGION, tuple) or len(BOARD_REGION) != 4 or any(v <= 0 for v in BOARD_REGION[2:]):
            self.status_label.configure(text="Status: Board region not set or invalid. Please select the region.")
            self.running = False
            # Offer to re-select region
            if hasattr(self, 'region_label'):
                self.region_label.configure(text="Board Region: Not Set", text_color="#ffb347")
            if tk.messagebox.askyesno("Select Board Region", "Board region is not set or invalid. Do you want to select the region now?"):
                self.select_region()
            return
        board_img = capture_board(BOARD_REGION)
        # Safeguard: check if screenshot is valid
        if board_img is None or board_img.size[0] == 0 or board_img.size[1] == 0:
            self.status_label.configure(text="Status: Invalid board region or screenshot. Please re-select region.")
            self.running = False
            if tk.messagebox.askyesno("Invalid Region", "Screenshot failed. Do you want to select the region again?"):
                self.select_region()
            return
        try:
            tiles = detect_tiles(board_img)
        except Exception as e:
            self.status_label.configure(text=f"Status: Error capturing board: {e}")
            self.running = False
            return
        # Classify each tile
        tile_results = []
        for r in range(TILE_ROWS):
            row_results = []
            for c in range(TILE_COLS):
                tile_img = tiles[r][c]
                tile_type = classify_tile(tile_img, self.color_refs)
                row_results.append(tile_type)
            tile_results.append(row_results)
        self.current_tile_results = tile_results
        bomb_tiles = predict_bomb_locations()
        self.draw_board(bomb_tiles, tile_results)
        # Find a safe tile to suggest
        safe_tile = None
        for r in range(TILE_ROWS):
            for c in range(TILE_COLS):
                if (r, c) not in bomb_tiles:
                    safe_tile = (r, c)
                    break
            if safe_tile:
                break
        if hasattr(self, 'overlay') and self.overlay:
            if safe_tile:
                self.overlay.update_tip(f"💡 Safe Move: Row {safe_tile[0]+1}, Col {safe_tile[1]+1}")
            else:
                self.overlay.update_tip("⚠️ No safe moves detected!")
        self.after_id = self.after(3000, self.run_prediction_loop)

    def log_round(self):
        if self.current_tile_results is not None:
            update_heatmap(self.current_tile_results)
            self.status_label.configure(text=f"Logged round! Total rounds: {total_games}")
        else:
            self.status_label.configure(text="No round data to log.")

def main():
    print("Dubibet Mines Predictor - Standalone App Mode")
    load_heatmap()
    from overlay_assistant import OverlayAssistant
    app = PredictorApp()
    # Launch overlay as Toplevel child of main app
    app.overlay = OverlayAssistant(app, initial_tip="AI Assistant Ready!")
    app.overlay.after(100, lambda: app.overlay.lift())
    # Force launch directly into predictor UI for debug
    try:
        app.config_frame.destroy()
    except Exception as e:
        print(f"[DEBUG] config_frame destroy skipped: {e}")
    print("[DEBUG] Launching predictor board UI directly...")
    app.setup_predictor_ui()
    app.mainloop()



if __name__ == "__main__":
    main()
