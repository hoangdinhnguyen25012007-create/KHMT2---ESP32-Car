import tkinter as tk
from tkinter import scrolledtext, ttk
import socket
import threading
import time


# ====================== GUI - ESP32 CAR CONTROL ======================
class EspCarGUI:
    # ── Màu sắc ──────────────────────────────────────────────────────
    BG          = "#0f0f17"
    PANEL       = "#1a1a2e"
    BTN         = "#16213e"
    BTN_HOVER   = "#0f3460"
    ACCENT      = "#00f5ff"
    RED         = "#ff006e"
    GREEN       = "#00ff9d"
    YELLOW      = "#ffd000"
    BLUE        = "#00b0ff"

    # Lệnh di chuyển tương ứng phím bấm
    KEY_MAP = {
        'w': 'F', 's': 'B', 'a': 'L', 'd': 'R',
        'Up': 'F', 'Down': 'B', 'Left': 'L', 'Right': 'R',
    }

    def __init__(self):
        self.sock: socket.socket | None = None
        self._connected = False

        self.root = tk.Tk()
        self.root.title("🚗 ESP32 CAR – WiFi Pro Control")
        self.root.geometry("700x820")
        self.root.configure(bg=self.BG)
        self.root.resizable(False, False)

        self._setup_styles()
        self._build_ui()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.log("🚀 GUI sẵn sàng – Nhập IP và kết nối!", "info")

    # ====================== SETUP ======================
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton",
                        background=self.BTN,
                        foreground="white",
                        font=("Arial", 10, "bold"))
        style.map("TButton", background=[('active', self.BTN_HOVER)])

    # ====================== BUILD UI ======================
    def _build_ui(self):
        self._build_connection_bar()
        self._build_distance_panel()
        self._build_control_pad()
        self._build_speed_panel()
        self._build_extras_panel()
        self._build_log_panel()

        self.root.bind("<KeyPress>",   self._key_press)
        self.root.bind("<KeyRelease>", self._key_release)

    def _build_connection_bar(self):
        frame = tk.Frame(self.root, bg=self.PANEL, height=70)
        frame.pack(fill="x", padx=12, pady=12)

        tk.Label(frame, text="🔌 KẾT NỐI ESP32",
                 bg=self.PANEL, fg=self.ACCENT,
                 font=("Arial", 12, "bold")).pack(side="left", padx=10)

        # IP
        tk.Label(frame, text="IP:", bg=self.PANEL, fg="white",
                 font=("Arial", 10)).pack(side="left", padx=(20, 5))
        self.ip_var = tk.StringVar(value="192.168.1.xxx")
        tk.Entry(frame, textvariable=self.ip_var, width=15,
                 bg=self.BTN, fg="white", relief="flat",
                 font=("Consolas", 11)).pack(side="left", padx=5)

        # Port
        tk.Label(frame, text="Port:", bg=self.PANEL, fg="white",
                 font=("Arial", 10)).pack(side="left", padx=(10, 5))
        self.port_var = tk.StringVar(value="8888")
        tk.Entry(frame, textvariable=self.port_var, width=6,
                 bg=self.BTN, fg="white", relief="flat",
                 font=("Consolas", 11)).pack(side="left", padx=5)

        tk.Button(frame, text="🔗 Kết nối", command=self.connect,
                  bg=self.GREEN, fg="black",
                  font=("Arial", 11, "bold"), relief="flat",
                  padx=15, pady=6).pack(side="left", padx=10)
        tk.Button(frame, text="⛔ Ngắt", command=self.disconnect,
                  bg=self.RED, fg="white",
                  font=("Arial", 11, "bold"), relief="flat",
                  padx=15, pady=6).pack(side="left")

        self.status_label = tk.Label(self.root,
                                     text="⚪ Chưa kết nối",
                                     bg=self.BG, fg=self.YELLOW,
                                     font=("Arial", 11, "bold"))
        self.status_label.pack(pady=5)

    def _build_distance_panel(self):
        frame = tk.Frame(self.root, bg=self.PANEL,
                         highlightbackground=self.ACCENT,
                         highlightthickness=2)
        frame.pack(pady=10, padx=20, fill="x")

        tk.Label(frame, text="📡 KHOẢNG CÁCH",
                 bg=self.PANEL, fg=self.ACCENT,
                 font=("Arial", 10, "bold")).pack(pady=(8, 0))

        self.dist_label = tk.Label(frame, text="Khoảng cách: -- cm",
                                   bg=self.PANEL, fg=self.GREEN,
                                   font=("Arial", 22, "bold"))
        self.dist_label.pack(pady=8)

    def _build_control_pad(self):
        ctrl = tk.Frame(self.root, bg=self.BG)
        ctrl.pack(pady=15)

        btn_cfg = {"width": 9, "height": 3,
                   "font": ("Arial", 14, "bold"),
                   "relief": "raised", "bd": 4}

        buttons = [
            ("▲\nTIẾN", 'F', self.GREEN,  "black", 0, 1),
            ("◀\nTRÁI", 'L', self.BLUE,   "black", 1, 0),
            ("⏹\nDỪNG", 'S', self.RED,    "white", 1, 1),
            ("▶\nPHẢI", 'R', self.BLUE,   "black", 1, 2),
            ("▼\nLÙI",  'B', self.GREEN,  "black", 2, 1),
        ]
        for text, cmd, bg, fg, row, col in buttons:
            tk.Button(ctrl, text=text, command=lambda c=cmd: self.send(c),
                      bg=bg, fg=fg, **btn_cfg).grid(
                row=row, column=col, padx=5, pady=5)

        # Emergency Stop
        tk.Button(self.root, text="🚨 EMERGENCY STOP",
                  command=lambda: self.send('S'),
                  bg=self.RED, fg="white",
                  font=("Arial", 14, "bold"),
                  relief="raised", bd=6, height=2).pack(
            pady=8, padx=40, fill="x")

    def _build_speed_panel(self):
        frame = tk.Frame(self.root, bg=self.PANEL)
        frame.pack(fill="x", padx=20, pady=8)

        tk.Label(frame, text="⚡ TỐC ĐỘ",
                 bg=self.PANEL, fg=self.YELLOW,
                 font=("Arial", 11, "bold")).pack(side="left", padx=15)

        self.speed_var = tk.IntVar(value=7)
        tk.Scale(frame, from_=1, to=9, orient="horizontal",
                 variable=self.speed_var,
                 command=self._on_speed_change,
                 length=320, bg=self.PANEL, fg="white",
                 troughcolor=self.BTN,
                 sliderlength=30).pack(side="left")

        tk.Label(frame, textvariable=self.speed_var,
                 bg=self.PANEL, fg=self.YELLOW,
                 font=("Arial", 16, "bold"), width=3).pack(side="left", padx=10)

    def _build_extras_panel(self):
        frame = tk.LabelFrame(self.root, text="💡 ĐÈN & ÂM THANH",
                              bg=self.PANEL, fg=self.ACCENT,
                              font=("Arial", 11, "bold"), labelanchor="n")
        frame.pack(fill="x", padx=20, pady=10)

        extras = [
            ("💡 Đèn pha ON",        'H', self.GREEN),
            ("💡 Đèn pha OFF",       'h', self.BTN),
            ("◀ Xi nhan Trái ON",    'Q', self.YELLOW),
            ("◀ Xi nhan Trái OFF",   'q', self.BTN),
            ("▶ Xi nhan Phải ON",    'E', self.YELLOW),
            ("▶ Xi nhan Phải OFF",   'e', self.BTN),
            ("📢 Còi thường ON",     'Z', "#ff8800"),
            ("📢 Còi thường OFF",    'z', self.BTN),
            ("🚨 Còi báo động ON",   'X', self.RED),
            ("🚨 Còi báo động OFF",  'x', self.BTN),
            ("🤖 Auto ON",           'A', self.BLUE),
            ("🤖 Auto OFF",          'a', self.BTN),
        ]

        for i, (text, cmd, color) in enumerate(extras):
            tk.Button(frame, text=text,
                      command=lambda c=cmd: self.send(c),
                      bg=color,
                      fg="black" if color != self.BTN else "white",
                      font=("Arial", 9, "bold"),
                      relief="flat", padx=12, pady=8).grid(
                row=i // 3, column=i % 3,
                padx=6, pady=6, sticky="ew")

        frame.columnconfigure((0, 1, 2), weight=1)

    def _build_log_panel(self):
        tk.Label(self.root, text="📋 LOG SỰ KIỆN",
                 bg=self.BG, fg=self.ACCENT,
                 font=("Arial", 11, "bold")).pack(
            anchor="w", padx=25, pady=(10, 2))

        self.log_box = scrolledtext.ScrolledText(
            self.root, height=9, state='disabled',
            bg="#11111b", fg="#cdd6f4",
            font=("Consolas", 10))
        self.log_box.pack(fill="x", padx=20, pady=(0, 15))

        self.log_box.tag_config("danger", foreground=self.RED)
        self.log_box.tag_config("info",   foreground=self.BLUE)
        self.log_box.tag_config("normal", foreground="#cdd6f4")

    # ====================== KẾT NỐI ======================
    def connect(self):
        ip   = self.ip_var.get().strip()
        port = int(self.port_var.get().strip())
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((ip, port))
            self.sock.settimeout(None)
            self._connected = True
            self.status_label.config(
                text=f"✅ Kết nối thành công: {ip}:{port}",
                fg=self.GREEN)
            self.log(f"✅ Kết nối WiFi OK: {ip}:{port}", "info")
            threading.Thread(target=self._receive_loop,
                             daemon=True).start()
        except Exception as e:
            self.status_label.config(text=f"❌ Lỗi: {e}", fg=self.RED)
            self.log(f"❌ Lỗi kết nối: {e}", "danger")
            self.sock = None

    def disconnect(self):
        self._connected = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except OSError:
                pass
            self.sock = None
        self.status_label.config(text="⚪ Đã ngắt kết nối", fg=self.YELLOW)
        self.log("⛔ Đã ngắt kết nối", "info")

    # ====================== GỬI LỆNH ======================
    def send(self, cmd: str):
        if not self._connected or not self.sock:
            self.log("⚠️ Chưa kết nối!", "danger")
            return
        try:
            self.sock.sendall(cmd.encode())
            self.log(f"📤 Gửi lệnh: [{cmd}]", "info")
        except OSError:
            self.log("❌ Mất kết nối khi gửi lệnh!", "danger")
            self.disconnect()

    def _on_speed_change(self, val):
        self.send(str(int(float(val))))

    # ====================== NHẬN DỮ LIỆU ======================
    def _receive_loop(self):
        buffer = ""
        while self._connected and self.sock:
            try:
                data = self.sock.recv(1024).decode('utf-8', errors='ignore')
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    self.root.after(0, self._handle_message, line)
            except OSError:
                break

        if self._connected:               # mất kết nối không chủ ý
            self.root.after(0, self._on_unexpected_disconnect)

    def _handle_message(self, line: str):
        if line.startswith("DIST:"):
            self._update_distance(line.split(":", 1)[1])
        elif line == "WARN:obstacle":
            self.log("⚠️ Vật cản phía trước! Xe dừng!", "danger")
        elif line == "WARN:crash":
            self.log("💥 Va chạm phát hiện!", "danger")
        elif line.startswith("AUTO:"):
            self.log(f"🤖 Auto: {line.split(':', 1)[1]}", "info")
        else:
            self.log(f"📨 ESP32: {line}", "normal")

    def _on_unexpected_disconnect(self):
        self.log("❌ Mất kết nối với xe!", "danger")
        self.disconnect()

    # ====================== CẬP NHẬT KHOẢNG CÁCH ======================
    def _update_distance(self, val: str):
        try:
            d = int(val)
            self.dist_label.config(text=f"Khoảng cách: {d} cm")
            if d < 20:
                self.dist_label.config(fg=self.RED)
            elif d < 40:
                self.dist_label.config(fg=self.YELLOW)
            else:
                self.dist_label.config(fg=self.GREEN)
        except ValueError:
            self.dist_label.config(text=f"Khoảng cách: {val} cm")

    # ====================== LOG ======================
    def log(self, msg: str, tag: str = "normal"):
        ts = time.strftime("%H:%M:%S")
        self.log_box.config(state='normal')
        self.log_box.insert(tk.END, f"[{ts}] {msg}\n", tag)
        self.log_box.see(tk.END)
        self.log_box.config(state='disabled')

    # ====================== PHÍM TẮT ======================
    def _key_press(self, event):
        cmd = self.KEY_MAP.get(event.keysym)
        if cmd:
            self.send(cmd)

    def _key_release(self, event):
        if event.keysym in self.KEY_MAP:
            self.send('S')

    # ====================== ĐÓNG CỬA SỔ ======================
    def _on_close(self):
        self.disconnect()
        self.root.destroy()


# ====================== CHẠY ======================
if __name__ == "__main__":
    app = EspCarGUI()
    app.root.mainloop()