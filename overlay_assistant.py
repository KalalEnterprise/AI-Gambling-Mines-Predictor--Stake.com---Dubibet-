import customtkinter as ctk
import tkinter as tk

class OverlayAssistant(ctk.CTkToplevel):
    def __init__(self, master, initial_tip="AI Assistant Ready!"):
        super().__init__(master)
        print("[DEBUG] OverlayAssistant created!")
        self.title("Mines AI Overlay Assistant")
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.92)
        # Center overlay on screen
        self.update_idletasks()
        w, h = 340, 180
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.resizable(True, True)
        self.minsize(340, 120)
        self.overrideredirect(False)  # Set True for borderless, False for debug
        self.configure(bg_color="#222831")
        # Use a clear, modern, semi-transparent look
        self.tip_label = ctk.CTkLabel(
            self,
            text=initial_tip,
            font=("Segoe UI", 16, "bold"),
            text_color="#e6faff",
            fg_color=("#23272e", "#181a20"),
            corner_radius=18,
            width=320,
            height=36
        )
        self.tip_label.pack(padx=10, pady=(10, 0), fill="x")

        # Transcript display (scrollable)
        self.transcript_frame = ctk.CTkFrame(self, fg_color="#181a20", corner_radius=10)
        self.transcript_frame.pack(padx=10, pady=(8, 0), fill="both", expand=True)
        self.transcript_text = tk.Text(self.transcript_frame, bg="#181a20", fg="#e6faff", font=("Segoe UI", 12), wrap="word", bd=0, relief="flat", height=3)
        self.transcript_text.pack(side="left", fill="both", expand=True)
        self.transcript_text.config(state="disabled")
        self.transcript_scroll = tk.Scrollbar(self.transcript_frame, command=self.transcript_text.yview)
        self.transcript_scroll.pack(side="right", fill="y")
        self.transcript_text["yscrollcommand"] = self.transcript_scroll.set

        # Suggestions placeholder
        self.suggestion_label = ctk.CTkLabel(self, text="Suggestions will appear here", font=("Segoe UI", 10), text_color="#bbbbbb", fg_color="#23272e", corner_radius=10, width=320, height=24)
        self.suggestion_label.pack(padx=10, pady=(2, 5), fill="x")

        self.close_btn = ctk.CTkButton(
            self,
            text="✖ Close",
            command=self.destroy,
            fg_color="#23272e",
            hover_color="#393e46",
            text_color="#bbbbbb",
            font=("Segoe UI", 11, "bold"),
            corner_radius=10,
            width=80,
            height=28
        )
        self.close_btn.place(x=240, y=60)

        # Allow window dragging by clicking anywhere
        self.bind('<ButtonPress-1>', self.start_move)
        self.bind('<B1-Motion>', self.do_move)
        self._drag_data = {'x': 0, 'y': 0}

    def start_move(self, event):
        self._drag_data['x'] = event.x
        self._drag_data['y'] = event.y

    def do_move(self, event):
        x = self.winfo_x() + event.x - self._drag_data['x']
        y = self.winfo_y() + event.y - self._drag_data['y']
        self.geometry(f'+{x}+{y}')

    def update_tip(self, new_tip):
        self.tip_label.configure(text=new_tip)

    def start_move(self, event):
        self._drag_data['x'] = event.x
