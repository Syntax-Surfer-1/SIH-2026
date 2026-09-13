"""
=========================================================================================
Project: Synchronizing Secure Data Transmission Through Human Tap
Version: 1.2 (Spacious Light Theme Edition)
Base: HCI2.py (Legacy Working Python GUI)
Fixes:
  - Completely resolved congested layout: spacious, modern, breathable card design
  - Resolved login button visibility: fully visible with auto-fitting responsive cards (no clipped hardcoded heights)
  - Clear vertical hierarchy (no label/text overlap)
  - Dedicated PIN Verification stage
  - Persistent Action Buttons: Re-Scan, COM Select, Logout
  - Windows High-DPI aware, crisp Segoe UI typography, zero external dependencies
=========================================================================================
"""

import sys
import os
import time
import queue
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports

# Enable Windows High-DPI Awareness for crisp typography and accurate geometry
try:
    if sys.platform == "win32":
        from ctypes import windll
        try:
            windll.user32.SetProcessDpiAwarenessContext(-4)  # Per-monitor V2 awareness
        except Exception:
            try:
                windll.shcore.SetProcessDpiAwareness(1)       # System DPI awareness
            except Exception:
                pass
except Exception:
    pass

# Admin Credentials (from original HCI2.py)
ADMIN_USER = "admin"
ADMIN_PASS = "123"

# Baud Rates
BAUD_RATES = ["115200", "9600", "38400", "57600"]
DEFAULT_BAUD = "115200"

# Spacious, Clean Modern Light Palette
BG_MAIN = "#f8fafc"        # Very soft cool-gray background (slate-50)
BG_SURFACE = "#ffffff"     # Crisp white card surface
BG_INPUT = "#ffffff"       # White input background
BG_HEADER = "#ffffff"      # Clean white header
BG_STEPPER = "#f1f5f9"     # Stepper bar background
BORDER_COLOR = "#cbd5e1"   # Crisp slate-300 border
BORDER_FOCUS = "#2563eb"   # Royal blue focus outline
TEXT_PRIMARY = "#0f172a"   # Slate-900 (deep readable charcoal/black)
TEXT_SECONDARY = "#64748b" # Slate-500 (clean muted gray)
ACCENT_BLUE = "#2563eb"    # Primary action blue
ACCENT_GREEN = "#16a34a"   # Success green
ACCENT_RED = "#dc2626"     # Danger/Error red
ACCENT_AMBER = "#d97706"   # Warning amber
ACCENT_CYAN = "#0284c7"    # Cyan/blue accent


class HumanTapGUI_V1_2:
    def __init__(self, root):
        self.root = root
        self.root.title("Human Tap | Secure Data Transmission V1.2")
        self.root.geometry("860x700")
        self.root.minsize(780, 620)
        self.root.configure(bg=BG_MAIN)

        # Serial State
        self.ser = None
        self.serial_thread = None
        self.stop_serial_event = threading.Event()
        self.serial_queue = queue.Queue()
        self.is_scanning = False
        self.current_port = ""
        self.current_baud = ""
        self.show_password_login = False
        self.show_pin_entry = False

        # Configure TTK Styles for Light Theme
        self._setup_ttk_styles()

        # Build Main Layout Container
        self.container = tk.Frame(self.root, bg=BG_MAIN)
        self.container.pack(fill="both", expand=True)

        # Top Header Bar
        self._build_header_bar()

        # Stepper Navigation Indicator
        self._build_stepper()

        # Content Area for Views (Spacious with generous breathing room)
        self.content_area = tk.Frame(self.container, bg=BG_MAIN)
        self.content_area.pack(fill="both", expand=True, padx=30, pady=(15, 10))

        # View Frames Dictionary
        self.views = {}
        self._build_login_view()
        self._build_com_select_view()
        self._build_scanning_view()
        self._build_pin_view()
        self._build_result_view()

        # Bottom Persistent Action Bar
        self._build_bottom_bar()

        # Start on Login View
        self.show_view("login")

        # Serial queue worker tick (thread safe)
        self.root.after(40, self._process_serial_queue)

        # Handle window closing cleanly
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _setup_ttk_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Configure Combobox style for light theme
        style.configure(
            "Light.TCombobox",
            fieldbackground=BG_INPUT,
            background="#f1f5f9",
            foreground=TEXT_PRIMARY,
            darkcolor=BORDER_COLOR,
            lightcolor=BORDER_COLOR,
            bordercolor=BORDER_COLOR,
            arrowcolor=TEXT_PRIMARY,
            padding=6,
            font=("Segoe UI", 10)
        )
        style.map("Light.TCombobox", fieldbackground=[("readonly", BG_INPUT)])

    # =========================================================================
    # Header Bar & Live Status
    # =========================================================================
    def _build_header_bar(self):
        self.header = tk.Frame(self.container, bg=BG_HEADER, height=58, padx=25, pady=12, bd=1, relief="solid")
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        # Title Brand
        lbl_brand = tk.Label(
            self.header,
            text="⚡ HUMAN TAP  |  SECURE DATA TRANSMISSION",
            font=("Segoe UI", 12, "bold"),
            bg=BG_HEADER,
            fg=ACCENT_BLUE
        )
        lbl_brand.pack(side="left")

        # Version Pill
        lbl_ver = tk.Label(
            self.header,
            text="V1.2",
            font=("Segoe UI", 9, "bold"),
            bg="#e2e8f0",
            fg="#475569",
            padx=10,
            pady=3
        )
        lbl_ver.pack(side="left", padx=12)

        # Hardware Status Pill on right
        self.lbl_hw_status = tk.Label(
            self.header,
            text="● HARDWARE DISCONNECTED",
            font=("Segoe UI", 9, "bold"),
            bg="#fee2e2",
            fg=ACCENT_RED,
            padx=14,
            pady=5,
            relief="flat"
        )
        self.lbl_hw_status.pack(side="right")

    # =========================================================================
    # Visual Stepper Bar
    # =========================================================================
    def _build_stepper(self):
        self.stepper_frame = tk.Frame(self.container, bg=BG_STEPPER, height=42, padx=20, bd=1, relief="solid")
        self.stepper_frame.pack(fill="x")
        self.stepper_frame.pack_propagate(False)

        self.step_labels = []
        steps = [
            ("1", "Admin Login"),
            ("2", "Port & Speed Setup"),
            ("3", "Hardware Scan"),
            ("4", "PIN Verification")
        ]

        center_box = tk.Frame(self.stepper_frame, bg=BG_STEPPER)
        center_box.pack(anchor="center", pady=8)

        for i, (num, title) in enumerate(steps):
            lbl_step = tk.Label(
                center_box,
                text=f"  {num}. {title}  ",
                font=("Segoe UI", 9, "bold"),
                bg=BG_STEPPER,
                fg=TEXT_SECONDARY,
                padx=8,
                pady=2
            )
            lbl_step.pack(side="left")
            self.step_labels.append(lbl_step)

            if i < len(steps) - 1:
                lbl_arr = tk.Label(center_box, text="➔", font=("Segoe UI", 9), bg=BG_STEPPER, fg="#94a3b8")
                lbl_arr.pack(side="left", padx=6)

    def _update_stepper(self, active_index):
        for i, lbl in enumerate(self.step_labels):
            if i == active_index:
                lbl.config(bg="#dbeafe", fg=ACCENT_BLUE)
            elif i < active_index:
                lbl.config(bg=BG_STEPPER, fg=ACCENT_GREEN)
            else:
                lbl.config(bg=BG_STEPPER, fg=TEXT_SECONDARY)

    # =========================================================================
    # Navigation View Switcher
    # =========================================================================
    def show_view(self, name):
        for view_name, frame in self.views.items():
            frame.pack_forget()

        if name == "login":
            self._update_stepper(0)
            self.views["login"].pack(fill="both", expand=True)
            self.entry_login_user.focus_set()
            self._set_bottom_buttons(visible=False)

        elif name == "com_select":
            self._update_stepper(1)
            self._refresh_com_ports()
            self.views["com_select"].pack(fill="both", expand=True)
            self._set_bottom_buttons(visible=False)

        elif name == "scanning":
            self._update_stepper(2)
            self.views["scanning"].pack(fill="both", expand=True)
            self._set_bottom_buttons(visible=True)

        elif name == "pin_entry":
            self._update_stepper(3)
            self.entry_pin.delete(0, "end")
            self.lbl_pin_err.config(text="")
            self.views["pin_entry"].pack(fill="both", expand=True)
            self.entry_pin.focus_set()
            self._set_bottom_buttons(visible=True)

        elif name == "result":
            self._update_stepper(3)
            self.views["result"].pack(fill="both", expand=True)
            self._set_bottom_buttons(visible=True)

    # =========================================================================
    # Screen 1: Admin Login View (Completely unclipped, auto-height, spacious!)
    # =========================================================================
    def _build_login_view(self):
        v = tk.Frame(self.content_area, bg=BG_MAIN)
        self.views["login"] = v

        # Centered Card without hardcoded height: automatically wraps its content!
        card = tk.Frame(
            v,
            bg=BG_SURFACE,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )
        card.pack(expand=True, pady=15, padx=20)

        # Card Inner Container with comfortable padding
        inner = tk.Frame(card, bg=BG_SURFACE, padx=45, pady=35)
        inner.pack(fill="both", expand=True)

        # Card Icon & Header
        lbl_icon = tk.Label(inner, text="🛡️", font=("Segoe UI", 32), bg=BG_SURFACE)
        lbl_icon.pack(pady=(0, 6))

        lbl_title = tk.Label(inner, text="Administrator Authentication", font=("Segoe UI", 16, "bold"), bg=BG_SURFACE, fg=TEXT_PRIMARY)
        lbl_title.pack(pady=(0, 4))

        lbl_sub = tk.Label(inner, text="Enter credentials to access Human Tap system", font=("Segoe UI", 10), bg=BG_SURFACE, fg=TEXT_SECONDARY)
        lbl_sub.pack(pady=(0, 24))

        # Form Container (Width 360px)
        form = tk.Frame(inner, bg=BG_SURFACE, width=360)
        form.pack(fill="x")

        # 1. User ID Row (Vertical: Label strictly above Entry field)
        lbl_u = tk.Label(form, text="Admin User ID", font=("Segoe UI", 10, "bold"), bg=BG_SURFACE, fg=TEXT_PRIMARY)
        lbl_u.pack(anchor="w", pady=(0, 5))

        self.entry_login_user = tk.Entry(
            form,
            font=("Segoe UI", 11),
            bg=BG_INPUT,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=BORDER_FOCUS
        )
        self.entry_login_user.insert(0, ADMIN_USER)
        self.entry_login_user.pack(fill="x", ipady=7, pady=(0, 16))

        # 2. Password Row (Vertical: Label strictly above Entry field)
        lbl_p = tk.Label(form, text="Master Password", font=("Segoe UI", 10, "bold"), bg=BG_SURFACE, fg=TEXT_PRIMARY)
        lbl_p.pack(anchor="w", pady=(0, 5))

        f_pass = tk.Frame(form, bg=BG_SURFACE)
        f_pass.pack(fill="x", pady=(0, 10))

        self.entry_login_pass = tk.Entry(
            f_pass,
            font=("Segoe UI", 11),
            show="●",
            bg=BG_INPUT,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=BORDER_FOCUS
        )
        self.entry_login_pass.insert(0, ADMIN_PASS)
        self.entry_login_pass.pack(side="left", fill="x", expand=True, ipady=7)

        # Eye toggle button
        self.btn_toggle_eye = tk.Button(
            f_pass,
            text="👁",
            font=("Segoe UI", 11),
            bg="#f8fafc",
            fg=TEXT_SECONDARY,
            activebackground="#e2e8f0",
            activeforeground=TEXT_PRIMARY,
            bd=1,
            relief="solid",
            command=self._toggle_password_view,
            width=3
        )
        self.btn_toggle_eye.pack(side="left", padx=(6, 0), ipady=4)

        # Enter key triggers login
        self.entry_login_pass.bind("<Return>", lambda e: self._login_user())
        self.entry_login_user.bind("<Return>", lambda e: self.entry_login_pass.focus_set())

        # Error Text
        self.lbl_login_err = tk.Label(inner, text="", font=("Segoe UI", 9, "bold"), bg=BG_SURFACE, fg=ACCENT_RED)
        self.lbl_login_err.pack(pady=(4, 12))

        # Login Button (Fully visible, prominent, spacious!)
        btn_login = tk.Button(
            inner,
            text="Login & Unlock System ➔",
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT_BLUE,
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            bd=0,
            cursor="hand2",
            command=self._login_user
        )
        btn_login.pack(fill="x", ipady=10, pady=(0, 10))

    def _toggle_password_view(self):
        self.show_password_login = not self.show_password_login
        if self.show_password_login:
            self.entry_login_pass.config(show="")
            self.btn_toggle_eye.config(text="🔒")
        else:
            self.entry_login_pass.config(show="●")
            self.btn_toggle_eye.config(text="👁")

    def _login_user(self):
        uid = self.entry_login_user.get().strip()
        pwd = self.entry_login_pass.get().strip()

        if uid == ADMIN_USER and pwd == ADMIN_PASS:
            self.lbl_login_err.config(text="")
            self._log_terminal("[ADMIN] Login verified successfully.")
            self.show_view("com_select")
        else:
            self.lbl_login_err.config(text="❌ Invalid User ID or Password (default: admin / 123)")

    # =========================================================================
    # Screen 2: Port & Speed Setup View (Spacious auto-height card)
    # =========================================================================
    def _build_com_select_view(self):
        v = tk.Frame(self.content_area, bg=BG_MAIN)
        self.views["com_select"] = v

        card = tk.Frame(
            v,
            bg=BG_SURFACE,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )
        card.pack(expand=True, pady=15, padx=20)

        inner = tk.Frame(card, bg=BG_SURFACE, padx=50, pady=35)
        inner.pack(fill="both", expand=True)

        # Header
        lbl_icon = tk.Label(inner, text="🔌", font=("Segoe UI", 32), bg=BG_SURFACE)
        lbl_icon.pack(pady=(0, 6))

        lbl_title = tk.Label(inner, text="Hardware Serial Connection", font=("Segoe UI", 16, "bold"), bg=BG_SURFACE, fg=TEXT_PRIMARY)
        lbl_title.pack(pady=(0, 4))

        lbl_sub = tk.Label(inner, text="Select the Arduino USB communication port and baud speed", font=("Segoe UI", 10), bg=BG_SURFACE, fg=TEXT_SECONDARY)
        lbl_sub.pack(pady=(0, 24))

        form = tk.Frame(inner, bg=BG_SURFACE, width=400)
        form.pack(fill="x")

        # COM Port Row (Vertical Label ABOVE input)
        lbl_port = tk.Label(form, text="Arduino Serial Port (COM)", font=("Segoe UI", 10, "bold"), bg=BG_SURFACE, fg=TEXT_PRIMARY)
        lbl_port.pack(anchor="w", pady=(0, 5))

        f_port = tk.Frame(form, bg=BG_SURFACE)
        f_port.pack(fill="x", pady=(0, 16))

        self.com_port_var = tk.StringVar()
        self.combo_ports = ttk.Combobox(f_port, textvariable=self.com_port_var, state="readonly", style="Light.TCombobox")
        self.combo_ports.pack(side="left", fill="x", expand=True, ipady=4)

        btn_refresh = tk.Button(
            f_port,
            text="🔄 Refresh",
            font=("Segoe UI", 9, "bold"),
            bg="#f1f5f9",
            fg=TEXT_PRIMARY,
            activebackground="#e2e8f0",
            activeforeground=TEXT_PRIMARY,
            bd=1,
            relief="solid",
            cursor="hand2",
            command=self._refresh_com_ports,
            padx=12
        )
        btn_refresh.pack(side="left", padx=(8, 0), ipady=4)

        # Baud Rate Row (Vertical Label ABOVE input)
        lbl_baud = tk.Label(form, text="Communication Speed (Baud Rate)", font=("Segoe UI", 10, "bold"), bg=BG_SURFACE, fg=TEXT_PRIMARY)
        lbl_baud.pack(anchor="w", pady=(0, 5))

        self.baud_rate_var = tk.StringVar(value=DEFAULT_BAUD)
        self.combo_baud = ttk.Combobox(form, textvariable=self.baud_rate_var, values=BAUD_RATES, state="readonly", style="Light.TCombobox")
        self.combo_baud.pack(fill="x", ipady=4, pady=(0, 24))

        # Action Buttons Row
        f_btn = tk.Frame(inner, bg=BG_SURFACE)
        f_btn.pack(fill="x", pady=(5, 5))

        btn_connect = tk.Button(
            f_btn,
            text="Connect & Begin Scanning ➔",
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT_GREEN,
            fg="#ffffff",
            activebackground="#15803d",
            activeforeground="#ffffff",
            bd=0,
            cursor="hand2",
            command=self._start_scan_connection
        )
        btn_connect.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 10))

        btn_logout = tk.Button(
            f_btn,
            text="Logout",
            font=("Segoe UI", 10, "bold"),
            bg="#fee2e2",
            fg=ACCENT_RED,
            activebackground="#fecaca",
            activeforeground=ACCENT_RED,
            bd=1,
            relief="solid",
            cursor="hand2",
            command=self.logout,
            padx=16
        )
        btn_logout.pack(side="left", ipady=9)

    def _refresh_com_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if ports:
            self.combo_ports['values'] = ports
            if self.com_port_var.get() not in ports:
                self.com_port_var.set(ports[0])
        else:
            self.combo_ports['values'] = ["No COM Ports Found"]
            self.com_port_var.set("No COM Ports Found")

    # =========================================================================
    # Screen 3: Scanning View (Spacious layout, clean proportions)
    # =========================================================================
    def _build_scanning_view(self):
        v = tk.Frame(self.content_area, bg=BG_MAIN)
        self.views["scanning"] = v

        # Hero Status Card
        hero_card = tk.Frame(
            v,
            bg=BG_SURFACE,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            padx=35,
            pady=25
        )
        hero_card.pack(fill="x", pady=(0, 15))

        lbl_radar = tk.Label(hero_card, text="📡", font=("Segoe UI", 36), bg=BG_SURFACE)
        lbl_radar.pack(pady=(0, 6))

        lbl_status_head = tk.Label(
            hero_card,
            text="SENSOR SCANNING ACTIVE",
            font=("Segoe UI", 16, "bold"),
            bg=BG_SURFACE,
            fg=ACCENT_CYAN
        )
        lbl_status_head.pack(pady=(0, 6))

        lbl_desc = tk.Label(
            hero_card,
            text="Awaiting touch on 4-wire resistive matrix & HFC card...\nPlace your finger and tag on the sensor to initiate secure transmission.",
            font=("Segoe UI", 10),
            bg=BG_SURFACE,
            fg=TEXT_SECONDARY,
            justify="center"
        )
        lbl_desc.pack(pady=(0, 16))

        # Clean Status Pill
        self.lbl_scan_badge = tk.Label(
            hero_card,
            text="● LISTENING FOR HUMAN TAP ●",
            font=("Consolas", 11, "bold"),
            bg="#e0f2fe",
            fg=ACCENT_CYAN,
            padx=20,
            pady=8,
            bd=1,
            relief="solid"
        )
        self.lbl_scan_badge.pack()

        # Terminal Card (Dedicated, clean, not crowded)
        term_card = tk.Frame(
            v,
            bg=BG_SURFACE,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            padx=25,
            pady=18
        )
        term_card.pack(fill="both", expand=True)

        f_top_term = tk.Frame(term_card, bg=BG_SURFACE)
        f_top_term.pack(fill="x", pady=(0, 8))

        lbl_t = tk.Label(f_top_term, text="Live Serial Telemetry Console", font=("Segoe UI", 10, "bold"), bg=BG_SURFACE, fg=TEXT_PRIMARY)
        lbl_t.pack(side="left")

        btn_clear = tk.Button(
            f_top_term,
            text="Clear Log",
            font=("Segoe UI", 8),
            bg="#f1f5f9",
            fg=TEXT_SECONDARY,
            bd=1,
            relief="solid",
            cursor="hand2",
            command=self._clear_terminal,
            padx=8
        )
        btn_clear.pack(side="right")

        self.term_box = tk.Text(
            term_card,
            font=("Consolas", 9),
            bg="#f8fafc",
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            wrap="word"
        )
        self.term_box.pack(fill="both", expand=True)

    def _clear_terminal(self):
        try:
            self.term_box.delete("1.0", "end")
        except Exception:
            pass

    # =========================================================================
    # Screen 4: Dedicated PIN Verification Card (Spacious, Zero Overlap!)
    # =========================================================================
    def _build_pin_view(self):
        v = tk.Frame(self.content_area, bg=BG_MAIN)
        self.views["pin_entry"] = v

        card = tk.Frame(
            v,
            bg=BG_SURFACE,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )
        card.pack(expand=True, pady=15, padx=20)

        inner = tk.Frame(card, bg=BG_SURFACE, padx=55, pady=35)
        inner.pack(fill="both", expand=True)

        # Icon & Touch Detected Alert
        lbl_icon = tk.Label(inner, text="🔑", font=("Segoe UI", 34), bg=BG_SURFACE)
        lbl_icon.pack(pady=(0, 6))

        lbl_touch_head = tk.Label(
            inner,
            text="Human Tap Detected!",
            font=("Segoe UI", 17, "bold"),
            bg=BG_SURFACE,
            fg=ACCENT_GREEN
        )
        lbl_touch_head.pack(pady=(0, 4))

        lbl_touch_sub = tk.Label(
            inner,
            text="Hardware touch verified. Enter security PIN to complete authentication:",
            font=("Segoe UI", 10),
            bg=BG_SURFACE,
            fg=TEXT_SECONDARY
        )
        lbl_touch_sub.pack(pady=(0, 24))

        # PIN Entry Container (Clear vertical hierarchy: NO OVERLAPPING GUARANTEED)
        form_pin = tk.Frame(inner, bg=BG_SURFACE, width=380)
        form_pin.pack(fill="x")

        # Label strictly above entry field
        lbl_pin_text = tk.Label(
            form_pin,
            text="Security PIN Code",
            font=("Segoe UI", 10, "bold"),
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY
        )
        lbl_pin_text.pack(anchor="w", pady=(0, 6))

        # Centered spacious Entry Box
        f_entry_row = tk.Frame(form_pin, bg=BG_SURFACE)
        f_entry_row.pack(fill="x", pady=(0, 8))

        self.entry_pin = tk.Entry(
            f_entry_row,
            font=("Segoe UI", 15, "bold"),
            justify="center",
            show="●",
            bg=BG_INPUT,
            fg=ACCENT_BLUE,
            insertbackground=TEXT_PRIMARY,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=BORDER_FOCUS
        )
        self.entry_pin.pack(side="left", fill="x", expand=True, ipady=9)

        # Toggle PIN mask eye
        btn_eye_pin = tk.Button(
            f_entry_row,
            text="👁",
            font=("Segoe UI", 11),
            bg="#f8fafc",
            fg=TEXT_SECONDARY,
            activebackground="#e2e8f0",
            activeforeground=TEXT_PRIMARY,
            bd=1,
            relief="solid",
            command=self._toggle_pin_view,
            width=3
        )
        btn_eye_pin.pack(side="left", padx=(8, 0), ipady=6)

        # Enter key triggers PIN submission
        self.entry_pin.bind("<Return>", lambda e: self._submit_pin())

        # Error / Feedback label
        self.lbl_pin_err = tk.Label(inner, text="", font=("Segoe UI", 10, "bold"), bg=BG_SURFACE, fg=ACCENT_RED)
        self.lbl_pin_err.pack(pady=(4, 14))

        # Submit PIN Button (Large, unclipped, prominent!)
        btn_submit = tk.Button(
            inner,
            text="Verify & Submit PIN ➔",
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT_BLUE,
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            bd=0,
            cursor="hand2",
            command=self._submit_pin
        )
        btn_submit.pack(fill="x", ipady=10, pady=(0, 10))

    def _toggle_pin_view(self):
        self.show_pin_entry = not self.show_pin_entry
        if self.show_pin_entry:
            self.entry_pin.config(show="")
        else:
            self.entry_pin.config(show="●")

    # =========================================================================
    # Screen 5: Result View (Spacious auto-height card)
    # =========================================================================
    def _build_result_view(self):
        v = tk.Frame(self.content_area, bg=BG_MAIN)
        self.views["result"] = v

        card = tk.Frame(
            v,
            bg=BG_SURFACE,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )
        card.pack(expand=True, pady=15, padx=20)

        inner = tk.Frame(card, bg=BG_SURFACE, padx=55, pady=35)
        inner.pack(fill="both", expand=True)

        self.lbl_result_icon = tk.Label(inner, text="✅", font=("Segoe UI", 42), bg=BG_SURFACE)
        self.lbl_result_icon.pack(pady=(0, 6))

        self.lbl_result_title = tk.Label(inner, text="ACCESS GRANTED", font=("Segoe UI", 18, "bold"), bg=BG_SURFACE, fg=ACCENT_GREEN)
        self.lbl_result_title.pack(pady=(0, 6))

        self.lbl_result_sub = tk.Label(
            inner,
            text="Secure Data Transmission Synchronized Successfully via Human Tap",
            font=("Segoe UI", 10),
            bg=BG_SURFACE,
            fg=TEXT_SECONDARY
        )
        self.lbl_result_sub.pack(pady=(0, 22))

        # Information Box (Light Card)
        info_box = tk.Frame(inner, bg="#f8fafc", bd=1, relief="solid", highlightthickness=1, highlightbackground=BORDER_COLOR, padx=24, pady=18)
        info_box.pack(fill="x", pady=(0, 22))

        self.lbl_info_status = tk.Label(info_box, text="Status: Clearance Level 5 Verified", font=("Segoe UI", 10, "bold"), bg="#f8fafc", fg=TEXT_PRIMARY)
        self.lbl_info_status.pack(anchor="w", pady=3)

        self.lbl_info_time = tk.Label(info_box, text="Timestamp: --", font=("Consolas", 10), bg="#f8fafc", fg=TEXT_SECONDARY)
        self.lbl_info_time.pack(anchor="w", pady=3)

        self.lbl_info_device = tk.Label(info_box, text="Hardware: Synchronized via 115200 Baud Link", font=("Segoe UI", 9), bg="#f8fafc", fg=ACCENT_BLUE)
        self.lbl_info_device.pack(anchor="w", pady=3)

        # Quick Re-Scan Button on Card
        btn_card_rescan = tk.Button(
            inner,
            text="🔄 Next / Re-Scan Tap",
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT_GREEN,
            fg="#ffffff",
            activebackground="#15803d",
            activeforeground="#ffffff",
            bd=0,
            cursor="hand2",
            command=self.rescan
        )
        btn_card_rescan.pack(fill="x", ipady=10)

    # =========================================================================
    # Persistent Bottom Action Bar (Spacious, comfortable padding)
    # =========================================================================
    def _build_bottom_bar(self):
        self.bottom_bar = tk.Frame(self.container, bg=BG_HEADER, height=60, padx=25, pady=10, bd=1, relief="solid")
        self.bottom_bar.pack(fill="x", side="bottom")
        self.bottom_bar.pack_propagate(False)

        # 1. Re-scan Button (Resets scan without losing connection or login!)
        self.btn_bottom_rescan = tk.Button(
            self.bottom_bar,
            text="🔄 Re-Scan Tap",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT_CYAN,
            fg="#ffffff",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            bd=0,
            cursor="hand2",
            padx=18,
            command=self.rescan
        )
        self.btn_bottom_rescan.pack(side="left", padx=(0, 12), ipady=5)

        # 2. COM Select Button (Change COM port or speed cleanly)
        self.btn_bottom_com = tk.Button(
            self.bottom_bar,
            text="🔌 COM Select",
            font=("Segoe UI", 10, "bold"),
            bg="#f1f5f9",
            fg=ACCENT_AMBER,
            activebackground="#e2e8f0",
            activeforeground=ACCENT_AMBER,
            bd=1,
            relief="solid",
            cursor="hand2",
            padx=16,
            command=self.com_select
        )
        self.btn_bottom_com.pack(side="left", padx=6, ipady=5)

        # 3. Logout Button (Clears session back to Admin Login)
        self.btn_bottom_logout = tk.Button(
            self.bottom_bar,
            text="🚪 Logout",
            font=("Segoe UI", 10, "bold"),
            bg="#fef2f2",
            fg=ACCENT_RED,
            activebackground="#fee2e2",
            activeforeground=ACCENT_RED,
            bd=1,
            relief="solid",
            cursor="hand2",
            padx=16,
            command=self.logout
        )
        self.btn_bottom_logout.pack(side="right", ipady=5)

    def _set_bottom_buttons(self, visible=True):
        if visible:
            self.bottom_bar.pack(fill="x", side="bottom")
        else:
            self.bottom_bar.pack_forget()

    # =========================================================================
    # Serial Connection & Non-Blocking Worker Thread
    # =========================================================================
    def _start_scan_connection(self):
        selected_com = self.com_port_var.get()
        selected_baud = self.baud_rate_var.get()

        if not selected_com or "No COM" in selected_com:
            messagebox.showerror("Error", "Please select a valid COM port.\nIf your Arduino is connected, click 'Refresh'.")
            return

        if not selected_baud:
            messagebox.showerror("Error", "Please select a baud rate.")
            return

        self._disconnect_serial()

        try:
            baud_int = int(selected_baud)
            self.ser = serial.Serial(selected_com, baud_int, timeout=1)
            time.sleep(0.5)  # Let Arduino auto-reset settle

            self.current_port = selected_com
            self.current_baud = selected_baud
            self.lbl_hw_status.config(
                text=f"● CONNECTED: {self.current_port} ({self.current_baud})",
                bg="#dcfce7",
                fg=ACCENT_GREEN
            )

            # Start background serial worker
            self.stop_serial_event.clear()
            self.serial_thread = threading.Thread(target=self._serial_worker, daemon=True)
            self.serial_thread.start()

            # Switch to Scanning View
            self.show_view("scanning")
            self._log_terminal(f"[INFO] Opened connection to {selected_com} at {selected_baud} baud.")

        except serial.SerialException as e:
            messagebox.showerror("Connection Error", f"Could not connect to {selected_com}:\n{e}")
            self._log_terminal(f"[ERROR] Failed to open {selected_com}: {e}")

    def _disconnect_serial(self):
        self.stop_serial_event.set()
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None
        self.is_scanning = False
        self.lbl_hw_status.config(
            text="● HARDWARE DISCONNECTED",
            bg="#fee2e2",
            fg=ACCENT_RED
        )

    def _serial_worker(self):
        """Background thread reading serial lines to eliminate Tkinter GUI freeze."""
        while not self.stop_serial_event.is_set():
            if self.ser and self.ser.is_open:
                try:
                    if self.ser.in_waiting > 0:
                        raw = self.ser.readline().decode('utf-8', errors='replace').strip()
                        if raw:
                            self.serial_queue.put(("DATA", raw))
                    else:
                        time.sleep(0.04)
                except Exception as e:
                    self.serial_queue.put(("ERROR", str(e)))
                    break
            else:
                break

    def _process_serial_queue(self):
        """Thread-safe consumer for serial events on Tkinter main loop."""
        while not self.serial_queue.empty():
            try:
                msg_type, payload = self.serial_queue.get_nowait()
                if msg_type == "DATA":
                    self._log_terminal(f"[RX] {payload}")
                    self._handle_device_message(payload)
                elif msg_type == "ERROR":
                    self._log_terminal(f"[SERIAL ERROR] {payload}")
                    messagebox.showerror("Serial Communication Error", f"Device error:\n{payload}")
                    self.com_select()
            except queue.Empty:
                break

        self.root.after(40, self._process_serial_queue)

    def _log_terminal(self, text):
        now = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{now}] {text}\n"
        try:
            self.term_box.insert("end", formatted)
            self.term_box.see("end")
        except Exception:
            pass

    # =========================================================================
    # Protocol Signal Handler (Exact signals from GUI.ino / Arduino_V1_2.ino)
    # =========================================================================
    def _handle_device_message(self, data):
        # 1. "Touch Found" -> Transition to PIN View
        if "Touch Found" in data:
            self._log_terminal("[EVENT] Touch Found! Opening PIN Verification...")
            self.show_view("pin_entry")

        # 2. "Correct Pin" -> Access Granted
        elif "Correct Pin" in data:
            self._log_terminal("[EVENT] PIN verified! Access Granted.")
            self._show_access_granted()

        # 3. "Incorrect Pin" -> Access Denied
        elif "Incorrect Pin" in data:
            self._log_terminal("[EVENT] Incorrect PIN received.")
            self._show_access_denied()

        # 4. "Wrong Touch" -> Wrong touch detected
        elif "Wrong Touch" in data:
            self._log_terminal("[WARN] Unauthorized UID or Wrong Touch detected.")
            self._show_wrong_touch()

        # 5. "PIN Timeout"
        elif "PIN Timeout" in data:
            self._log_terminal("[WARN] Device PIN timeout expired.")
            self.lbl_pin_err.config(text="⏳ PIN Entry Timed Out. Please tap again.")

    def _submit_pin(self):
        pin = self.entry_pin.get().strip()
        if not pin:
            self.lbl_pin_err.config(text="⚠️ Please enter PIN code.")
            return

        if not pin.isdigit():
            self.lbl_pin_err.config(text="⚠️ PIN must contain digits only.")
            return

        if self.ser and self.ser.is_open:
            try:
                self._log_terminal(f"[TX] Submitting PIN: {pin}")
                self.ser.write(f"{pin}\n".encode('utf-8'))
                self.lbl_pin_err.config(text="Verifying PIN with device...", fg=ACCENT_BLUE)
            except Exception as e:
                self.lbl_pin_err.config(text=f"Serial transmit error: {e}", fg=ACCENT_RED)
        else:
            self.lbl_pin_err.config(text="Hardware not connected.", fg=ACCENT_RED)

    def _show_access_granted(self):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.lbl_result_icon.config(text="✅")
        self.lbl_result_title.config(text="ACCESS GRANTED", fg=ACCENT_GREEN)
        self.lbl_result_sub.config(text="Secure Data Transmission Synchronized Successfully via Human Tap")
        self.lbl_info_status.config(text="Status: Clearance Level 5 Verified", fg=ACCENT_GREEN)
        self.lbl_info_time.config(text=f"Timestamp: {now_str}")
        self.lbl_info_device.config(text=f"Hardware: Connected to {self.current_port} @ {self.current_baud} baud", fg=ACCENT_BLUE)
        self.show_view("result")

    def _show_access_denied(self):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.lbl_result_icon.config(text="❌")
        self.lbl_result_title.config(text="ACCESS DENIED", fg=ACCENT_RED)
        self.lbl_result_sub.config(text="Incorrect Security PIN. Authorization rejected by device.")
        self.lbl_info_status.config(text="Status: Authentication Failed", fg=ACCENT_RED)
        self.lbl_info_time.config(text=f"Timestamp: {now_str}")
        self.lbl_info_device.config(text="Action: Click 'Re-Scan Tap' below to attempt again.", fg=ACCENT_AMBER)
        self.show_view("result")

    def _show_wrong_touch(self):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.lbl_result_icon.config(text="⚠️")
        self.lbl_result_title.config(text="WRONG TOUCH DETECTED", fg=ACCENT_AMBER)
        self.lbl_result_sub.config(text="Unauthorized HFC UID or unapproved touch matrix pattern.")
        self.lbl_info_status.config(text="Status: Security Alert (Tag Rejected)", fg=ACCENT_AMBER)
        self.lbl_info_time.config(text=f"Timestamp: {now_str}")
        self.lbl_info_device.config(text="Action: Verify your tag credentials and re-scan.", fg=TEXT_SECONDARY)
        self.show_view("result")

    # =========================================================================
    # Persistent Actions: Re-Scan, COM Select, Logout
    # =========================================================================
    def rescan(self):
        """
        Re-Scan Tap:
        Clears previous scan/PIN state and returns to Scanning View
        WITHOUT disconnecting or logging out!
        """
        self._log_terminal("--- Re-Scan Initiated: Ready for next tap ---")
        if self.ser and self.ser.is_open:
            try:
                self.ser.reset_input_buffer()
            except Exception:
                pass

        self.entry_pin.delete(0, "end")
        self.lbl_pin_err.config(text="")
        self.show_view("scanning")

    def com_select(self):
        """
        COM Select:
        Closes current serial link and returns to Port & Speed selection
        while maintaining authenticated admin session.
        """
        self._disconnect_serial()
        self.show_view("com_select")

    def logout(self):
        """
        Logout:
        Disconnects hardware and returns to Admin Login.
        """
        self._disconnect_serial()
        self.entry_login_pass.delete(0, "end")
        self.lbl_login_err.config(text="")
        self.show_view("login")

    def _on_window_close(self):
        self._disconnect_serial()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = HumanTapGUI_V1_2(root)
    root.mainloop()
