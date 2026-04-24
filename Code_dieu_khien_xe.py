import tkinter as tk
from tkinter import scrolledtext, ttk
import socket
import threading
import time

# ====================== GUI - ESP32 CAR CONTROL ======================
class EspCarGUI:
    def __init__(self):
        self.sock = None
        self.root = tk.Tk()
        self.root.title("🚗 ESP32 CAR - WiFi Pro Control")
        self.root.geometry("700x820")
        self.root.configure(bg="#0f0f17")
        self.root.resizable(False, False)

        # ==================== MÀU SẮC NEO NHIỆT ====================
        self.BG = "#0f0f17"
        self.PANEL = "#1a1a2e"
        self.BTN = "#16213e"
        self.BTN_HOVER = "#0f3460"
        self.ACCENT = "#00f5ff"
        self.RED = "#ff006e"
        self.GREEN = "#00ff9d"
        self.YELLOW = "#ffd000"
        self.BLUE = "#00b0ff"

        self.setup_styles()
        self.build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.log("🚀 GUI sẵn sàng - Nhập IP và kết nối!", "info")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", background=self.BTN, foreground="white", font=("Arial", 10, "bold"))
        style.map("TButton", background=[('active', self.BTN_HOVER)])

    def build_ui(self):
        # ── TOP BAR: Kết nối ─────────────────────────────────────
        top_frame = tk.Frame(self.root, bg=self.PANEL, height=70)
        top_frame.pack(fill="x", padx=12, pady=12)

        tk.Label(top_frame, text="🔌 KẾT NỐI ESP32", bg=self.PANEL, fg=self.ACCENT,
                 font=("Arial", 12, "bold")).pack(side="left", padx=10)

        # IP & Port
        tk.Label(top_frame, text="IP:", bg=self.PANEL, fg="white", font=("Arial", 10)).pack(side="left", padx=(20,5))
        self.ip_var = tk.StringVar(value="192.168.1.xxx")
        tk.Entry(top_frame, textvariable=self.ip_var, width=15, bg="#16213e", fg="white",
                 relief="flat", font=("Consolas", 11)).pack(side="left", padx=5)

        tk.Label(top_frame, text="Port:", bg=self.PANEL, fg="white", font=("Arial", 10)).pack(side="left", padx=(10,5))
        self.port_var = tk.StringVar(value="8888")
        tk.Entry(top_frame, textvariable=self.port_var, width=6, bg="#16213e", fg="white",
                 relief="flat", font=("Consolas", 11)).pack(side="left", padx=5)

        tk.Button(top_frame, text="🔗 Kết nối", command=self.connect, bg=self.GREEN, fg="black",
                  font=("Arial", 11, "bold"), relief="flat", padx=15, pady=6).pack(side="left", padx=10)
        tk.Button(top_frame, text="⛔ Ngắt", command=self.disconnect, bg=self.RED, fg="white",
                  font=("Arial", 11, "bold"), relief="flat", padx=15, pady=6).pack(side="left")

        # Trạng thái
        self.status_label = tk.Label(self.root, text="⚪ Chưa kết nối", bg=self.BG, fg=self.YELLOW,
                                     font=("Arial", 11, "bold"))
        self.status_label.pack(pady=5)

        # ── DASHBOARD: Khoảng cách ─────────────────────────────────
        dist_frame = tk.Frame(self.root, bg=self.PANEL, relief="solid", bd=3, highlightbackground=self.ACCENT, highlightthickness=2)
        dist_frame.pack(pady=10, padx=20, fill="x")

        tk.Label(dist_frame, text="📡 KHOẢNG CÁCH", bg=self.PANEL, fg=self.ACCENT,
                 font=("Arial", 10, "bold")).pack(pady=(8,0))

        self.dist_label = tk.Label(dist_frame, text="Khoảng cách: -- cm", bg=self.PANEL,
                                   fg=self.GREEN, font=("Arial", 22, "bold"))
        self.dist_label.pack(pady=8)

        # ── ĐIỀU KHIỂN CHÍNH (Joystick style) ─────────────────────
        ctrl_frame = tk.Frame(self.root, bg=self.BG)
        ctrl_frame.pack(pady=15)

        btn_style = {"width": 9, "height": 3, "font": ("Arial", 14, "bold"), "relief": "raised", "bd": 4}

        tk.Button(ctrl_frame, text="▲\nTIẾN", command=lambda: self.send('F'), bg="#00ff9d", fg="black", **btn_style).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(ctrl_frame, text="◀\nTRÁI", command=lambda: self.send('L'), bg="#00b0ff", fg="black", **btn_style).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(ctrl_frame, text="⏹\nDỪNG", command=lambda: self.send('S'), bg=self.RED, fg="white", **btn_style).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(ctrl_frame, text="▶\nPHẢI", command=lambda: self.send('R'), bg="#00b0ff", fg="black", **btn_style).grid(row=1, column=2, padx=5, pady=5)
        tk.Button(ctrl_frame, text="▼\nLÙI", command=lambda: self.send('B'), bg="#00ff9d", fg="black", **btn_style).grid(row=2, column=1, padx=5, pady=5)

        # Emergency Stop lớn
        tk.Button(self.root, text="🚨 EMERGENCY STOP", command=lambda: self.send('S'), bg=self.RED, fg="white",
                  font=("Arial", 14, "bold"), relief="raised", bd=6, height=2).pack(pady=8, padx=40, fill="x")

        # ── TỐC ĐỘ ───────────────────────────────────────────────
        speed_frame = tk.Frame(self.root, bg=self.PANEL)
        speed_frame.pack(fill="x", padx=20, pady=8)

        tk.Label(speed_frame, text="⚡ TỐC ĐỘ", bg=self.PANEL, fg=self.YELLOW, font=("Arial", 11, "bold")).pack(side="left", padx=15)
        self.speed_var = tk.IntVar(value=7)
        tk.Scale(speed_frame, from_=1, to=9, orient="horizontal", variable=self.speed_var,
                 command=self.on_speed_change, length=320, bg=self.PANEL, fg="white",
                 troughcolor="#16213e", sliderlength=30).pack(side="left")
        tk.Label(speed_frame, textvariable=self.speed_var, bg=self.PANEL, fg=self.YELLOW,
                 font=("Arial", 16, "bold"), width=3).pack(side="left", padx=10)

        # ── CHỨC NĂNG PHỤ (Lights + Sounds) ───────────────────────
        func_frame = tk.LabelFrame(self.root, text="💡 ĐÈN & ÂM THANH", bg=self.PANEL, fg=self.ACCENT,
                                   font=("Arial", 11, "bold"), labelanchor="n")
        func_frame.pack(fill="x", padx=20, pady=10)

        extras = [
            ("💡 Đèn pha ON",  'H', self.GREEN),
            ("💡 Đèn pha OFF", 'h', self.BTN),
            ("◀ Xi nhan Trái", 'Q', self.YELLOW),
            ("Xi nhan Trái OFF", 'q', self.BTN),
            ("▶ Xi nhan Phải", 'E', self.YELLOW),
            ("Xi nhan Phải OFF", 'e', self.BTN),
            ("📢 Còi thường ON", 'Z', "#ff8800"),
            ("Còi thường OFF", 'z', self.BTN),
            ("🚨 CÒI BÁO ĐỘNG ON", 'X', self.RED),      # ← NÚT MỚI
            ("Còi báo động OFF", 'x', self.BTN),
            ("🤖 Auto ON", 'A', self.BLUE),
            ("Auto OFF", 'a', self.BTN),
        ]

        for i, (text, cmd, color) in enumerate(extras):
            tk.Button(func_frame, text=text, command=lambda c=cmd: self.send(c),
                      bg=color, fg="black" if color != self.BTN else "white",
                      font=("Arial", 9, "bold"), relief="flat", padx=12, pady=8).grid(
                row=i//3, column=i%3, padx=6, pady=6, sticky="ew")

        func_frame.columnconfigure((0,1,2), weight=1)

        # ── LOG ───────────────────────────────────────────────────
        tk.Label(self.root, text="📋 LOG SỰ KIỆN", bg=self.BG, fg=self.ACCENT,
                 font=("Arial", 11, "bold")).pack(anchor="w", padx=25, pady=(10,2))

        self.log_box = scrolledtext.ScrolledText(self.root, height=9, state='disabled',
                                                 bg="#11111b", fg="#cdd6f4", font=("Consolas", 9.5))
        self.log_box.pack(fill="x", padx=20, pady=(0,15))

        self.log_box.tag_config("danger", foreground=self.RED)
        self.log_box.tag_config("info",   foreground=self.BLUE)
        self.log_box.tag_config("normal", foreground="#cdd6f4")

        # Phím tắt
        self.root.bind("<KeyPress>", self.key_press)
        self.root.bind("<KeyRelease>", self.key_release)

    # ====================== CÁC HÀM CHÍNH ======================
    def connect(self):
        global sock
        ip = self.ip_var.get().strip()
        port = int(self.port_var.get().strip())
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((ip, port))
            self.sock.settimeout(None)
            self.status_label.config(text=f"✅ Kết nối thành công: {ip}:{port}", fg=self.GREEN)
            self.log(f"✅ Kết nối WiFi OK: {ip}:{port}", "info")

            threading.Thread(target=self.receive_loop, daemon=True).start()
        except Exception as e:
            self.status_label.config(text=f"❌ Lỗi: {e}", fg=self.RED)
            self.log(f"❌ Lỗi kết nối: {e}", "danger")

    def disconnect(self):
        if self.sock:
            try: self.sock.close()
            except: pass
            self.sock = None
        self.status_label.config(text="⚪ Đã ngắt kết nối", fg=self.YELLOW)
        self.log("⛔ Đã ngắt kết nối", "info")

    def send(self, cmd):
        if not self.sock:
            self.log("⚠️ Chưa kết nối!", "danger")
            return
        try:
            self.sock.sendall(cmd.encode())
            self.log(f"📤 Gửi lệnh: {cmd}", "info")
        except:
            self.log("❌ Mất kết nối khi gửi lệnh!", "danger")
            self.disconnect()

    def on_speed_change(self, val):
        self.send(str(int(float(val))))

    def receive_loop(self):
        buffer = ""
        while self.sock:
            try:
                data = self.sock.recv(1024).decode('utf-8', errors='ignore')
                if not data: break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line: continue

                    if line.startswith("DIST:"):
                        self.root.after(0, self.update_distance, line.split(":")[1])
                    elif line == "WARN:obstacle":
                        self.root.after(0, lambda: self.log("⚠️ Vật cản! Xe dừng!", "danger"))
                    elif line == "WARN:crash":
                        self.root.after(0, lambda: self.log("💥 Va chạm!", "danger"))
                    elif line.startswith("AUTO:"):
                        self.root.after(0, lambda m=line.split(":")[1]: self.log(f"🤖 Auto: {m}", "info"))
            except:
                break
        self.root.after(0, lambda: self.log("❌ Mất kết nối với xe!", "danger"))

    def update_distance(self, val):
        try:
            d = int(val)
            self.dist_label.config(text=f"Khoảng cách: {d} cm")
            if d < 20:
                self.dist_label.config(fg=self.RED)
            elif d < 40:
                self.dist_label.config(fg=self.YELLOW)
            else:
                self.dist_label.config(fg=self.GREEN)
        except:
            self.dist_label.config(text=f"Khoảng cách: {val}")

    def log(self, msg, tag="normal"):
        timestamp = time.strftime("%H:%M:%S")
        self.log_box.config(state='normal')
        self.log_box.insert(tk.END, f"[{timestamp}] {msg}\n", tag)
        self.log_box.see(tk.END)
        self.log_box.config(state='disabled')

    def key_press(self, e):
        keys = {'w':'F','s':'B','a':'L','d':'R', 'Up':'F','Down':'B','Left':'L','Right':'R'}
        if e.keysym in keys:
            self.send(keys[e.keysym])

    def key_release(self, e):
        if e.keysym in ('w','s','a','d','Up','Down','Left','Right'):
            self.send('S')

    def on_close(self):
        self.disconnect()
        self.root.destroy()

# ====================== CHẠY GUI ======================
if __name__ == "__main__":
    root = tk.Tk()  # dummy để after hoạt động
    root.withdraw()
    app = EspCarGUI()
    app.root.mainloop()