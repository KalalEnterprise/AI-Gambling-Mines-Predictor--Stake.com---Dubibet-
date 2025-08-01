import pyautogui
import pytesseract
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

def update_heatmap(tile_results):
    global heatmap, total_games
    for row in range(TILE_ROWS):
        for col in range(TILE_COLS):
            if tile_results[row][col] == 'mine':
                heatmap[row][col] += 1
    total_games += 1

def suggest_safe_tiles():
    # Suggest tiles with the lowest mine frequency
    min_val = np.min(heatmap)
    safe_tiles = np.argwhere(heatmap == min_val)
    return safe_tiles

class PredictorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dubibet Mines Predictor")
        self.geometry(f"600x600")
        self.resizable(False, False)
        self.running = False
        self.after_id = None
        self.setup_config_ui()

    def setup_config_ui(self):
        self.config_frame = tk.Frame(self)
        self.config_frame.pack(fill='both', expand=True)
        tk.Label(self.config_frame, text="Dubibet Mines Predictor Setup", font=('Arial', 16, 'bold')).pack(pady=10)
        self.rows_var = tk.IntVar(value=5)
        self.cols_var = tk.IntVar(value=5)
        self.mines_var = tk.IntVar(value=3)
        tk.Label(self.config_frame, text="Board Rows:").pack()
        tk.Entry(self.config_frame, textvariable=self.rows_var).pack()
        tk.Label(self.config_frame, text="Board Columns:").pack()
        tk.Entry(self.config_frame, textvariable=self.cols_var).pack()
        tk.Label(self.config_frame, text="Mine Count:").pack()
        tk.Entry(self.config_frame, textvariable=self.mines_var).pack()
        self.region_label = tk.Label(self.config_frame, text="Board Region: Not Set", fg='red')
        self.region_label.pack(pady=5)
        tk.Button(self.config_frame, text="Select Board Region", command=self.select_region).pack(pady=5)
        # Color pickers
        self.color_refs = {'unclicked': (200,200,200), 'gem': (0,255,0), 'mine': (255,0,0)}
        tk.Label(self.config_frame, text="Pick tile colors (click to sample)").pack(pady=5)
        self.color_labels = {}
        for t in ['unclicked','gem','mine']:
            btn = tk.Button(self.config_frame, text=f"Pick {t} color", command=lambda tt=t: self.pick_color(tt))
            btn.pack()
            lbl = tk.Label(self.config_frame, text=f"{t.title()} color: {self.color_refs[t]}")
            lbl.pack()
            self.color_labels[t] = lbl
        tk.Button(self.config_frame, text="Start Predictor", command=self.launch_predictor).pack(pady=10)

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
        self.region_label.config(text=f"Board Region: {BOARD_REGION}", fg='green')
        self.deiconify()

    def launch_predictor(self):
        global TILE_ROWS, TILE_COLS, MINE_COUNT, heatmap
        TILE_ROWS = self.rows_var.get()
        TILE_COLS = self.cols_var.get()
        MINE_COUNT = self.mines_var.get()
        heatmap = np.zeros((TILE_ROWS, TILE_COLS), dtype=int)
        self.config_frame.destroy()
        self.setup_predictor_ui()

    def setup_predictor_ui(self):
        self.geometry(f"{TILE_COLS*TILE_SIZE+200}x{TILE_ROWS*TILE_SIZE+80}")
        self.canvas = tk.Canvas(self, width=TILE_COLS*TILE_SIZE, height=TILE_ROWS*TILE_SIZE, bg='#222')
        self.canvas.place(x=10, y=60)
        self.status_label = tk.Label(self, text="Status: Ready", anchor='w')
        self.status_label.place(x=10, y=10)
        self.info_label = tk.Label(self, text=f"Board: {TILE_ROWS}x{TILE_COLS} | Mines: {MINE_COUNT}", anchor='w', font=('Arial', 12, 'bold'))
        self.info_label.place(x=10, y=35)
        self.start_btn = tk.Button(self, text="Start", command=self.start_predictor)
        self.start_btn.place(x=TILE_COLS*TILE_SIZE+30, y=80)
        self.pause_btn = tk.Button(self, text="Pause", command=self.pause_predictor)
        self.pause_btn.place(x=TILE_COLS*TILE_SIZE+30, y=120)

    def draw_board(self, safe_tiles, tile_results=None):
        self.canvas.delete('all')
        for row in range(TILE_ROWS):
            for col in range(TILE_COLS):
                x1, y1 = col*TILE_SIZE, row*TILE_SIZE
                x2, y2 = x1+TILE_SIZE, y1+TILE_SIZE
                # Determine fill based on tile type
                tile_type = None
                if tile_results:
                    tile_type = tile_results[row][col]
                if tile_type == 'gem':
                    fill = '#00ff00'
                elif tile_type == 'mine':
                    fill = '#ff0000'
                elif tile_type == 'unclicked':
                    fill = '#cccccc'
                else:
                    fill = '#444'
                outline = 'yellow' if [row, col] in safe_tiles.tolist() else 'white'
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=3)
                # Draw a symbol for gem/mine
                if tile_type == 'gem':
                    self.canvas.create_text((x1+x2)//2, (y1+y2)//2, text='💎', font=('Arial', 18))
                elif tile_type == 'mine':
                    self.canvas.create_text((x1+x2)//2, (y1+y2)//2, text='💣', font=('Arial', 18))
        self.info_label.config(text=f"Board: {TILE_ROWS}x{TILE_COLS} | Mines: {MINE_COUNT}")

    def start_predictor(self):
        self.running = True
        self.status_label.config(text="Status: Running")
        self.run_prediction_loop()

    def pause_predictor(self):
        self.running = False
        self.status_label.config(text="Status: Paused")
        if self.after_id:
            self.after_cancel(self.after_id)

    def run_prediction_loop(self):
        if not self.running:
            return
        if BOARD_REGION is None:
            self.status_label.config(text="Status: Set BOARD_REGION in code!")
            return
        board_img = capture_board(BOARD_REGION)
        # Safeguard: check if screenshot is valid
        if board_img is None or board_img.size[0] == 0 or board_img.size[1] == 0:
            self.status_label.config(text="Status: Invalid board region or screenshot. Please re-select region.")
            self.running = False
            return
        try:
            tiles = detect_tiles(board_img)
        except Exception as e:
            self.status_label.config(text=f"Status: Error capturing board: {e}")
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
        update_heatmap(tile_results)
        safe_tiles = suggest_safe_tiles()
        self.draw_board(safe_tiles, tile_results)
        self.after_id = self.after(3000, self.run_prediction_loop)

def main():
    print("Dubibet Mines Predictor - Standalone App Mode")
    app = PredictorApp()
    app.mainloop()

if __name__ == "__main__":
    main()
