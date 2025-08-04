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
        w, h = 340, 90
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.resizable(False, False)
        self.overrideredirect(False)  # Set True for borderless, False for debug
        self.configure(bg_color="#222831")
        # Use a clear, modern, semi-transparent look
        self.tip_label = ctk.CTkLabel(
            self,
            text=initial_tip,
            font=("Segoe UI", 16, "bold"),
            text_color="#e6faff",
            fg_color=("#23272e", "#181a20"),  # subtle dark, semi-transparent
            corner_radius=18,
            width=320,
            height=60
        )
        self.tip_label.pack(padx=10, pady=10, fill="both", expand=True)
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
    def update_tip(self, new_tip):
        self.tip_label.configure(text=new_tip)
