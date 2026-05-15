import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading
import time

BG          = "#f0f2f5"   
PANEL       = "#ffffff"  
PANEL2      = "#f8f9fa"   
PANEL3      = "#e8ecf1"   
BORDER      = "#d0d5dd"  
BTN_DARK    = "#e0e4ea"  
BTN_HOVER   = "#c8d0dc"   

CYAN        = "#0099cc"   
CYAN_DIM    = "#b3d9ff"   
CYAN_GLOW   = "#33bbff"   
GREEN       = "#00a86b"  
GREEN_DIM   = "#b3f0d4"   
RED         = "#d32f2f"   
RED_DIM     = "#ffcdd2"  
ORANGE      = "#e65100"   
ORANGE_DIM  = "#ffe0b2"   
YELLOW      = "#f9a825"   
YELLOW_DIM  = "#fff9c4"   
PURPLE      = "#7b1fa2"   
PURPLE_DIM  = "#e1bee7"   
WHITE       = "#1a1a2e"   
GRAY        = "#6b7280"
GRAY2       = "#9ca3af"
GRAY3       = "#4b5563"

FONT_TITLE  = ("Segoe UI", 18, "bold")
FONT_BIG    = ("Segoe UI", 13, "bold")
FONT_MED    = ("Segoe UI", 10, "bold")
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 9)
FONT_METRIC = ("Segoe UI", 28, "bold")

LOGIN_USER = "admin"
LOGIN_PASS = "admin"


toast_id = None

def show_toast(message, tag="info", duration=2500):
    """Hiển thị thông báo toast ở góc trên bên phải"""
    global toast_id
    if toast_id:
        try:
            root.after_cancel(toast_id)
        except:
            pass
        toast_id = None

    colors = {
        "info":    (CYAN, "#e0f2fe"),
        "danger":  (RED, "#ffe5e8"),
        "success": (GREEN, "#d4f5e0"),
        "warning": (ORANGE, "#fff0d4"),
    }
    fg_color, bg_color = colors.get(tag, (GRAY3, PANEL2))

    toast_label.config(text=f"  {message}  ", fg=fg_color, bg=bg_color)
    toast_frame.config(bg=bg_color)
    toast_label.update_idletasks()

    toast_id = root.after(duration, hide_toast)

def hide_toast():
    """Ẩn toast notification"""
    global toast_id
    toast_label.config(text="")
    toast_id = None


sock            = None
safe_mode_on    = False
horn_on         = False
police_on       = False
headlight_on    = False
left_signal_on  = False
right_signal_on = False
last_distance   = 999
police_flash_id = None
login_window    = None



def show_login_window():
    """Hiển thị cửa sổ đăng nhập"""
    global login_window
    
    root.withdraw()
    
    login_window = tk.Toplevel(root)
    login_window.title("ĐĂNG NHẬP — ESP32 RC CAR")
    login_window.geometry("400x400")
    login_window.configure(bg=PANEL)
    login_window.resizable(False, False)
    
    login_window.update_idletasks()
    x = (login_window.winfo_screenwidth() - 400) // 2
    y = (login_window.winfo_screenheight() - 400) // 2
    login_window.geometry(f"400x400+{x}+{y}")
    
    login_window.protocol("WM_DELETE_WINDOW", lambda: None)
    
    icon_label = tk.Label(login_window, text="🚗", bg=PANEL, fg=CYAN,
                          font=("Segoe UI", 48))
    icon_label.pack(pady=(25, 5))
    
    tk.Label(login_window, text="ESP32 RC CAR", bg=PANEL, fg=CYAN,
             font=FONT_TITLE).pack()
    tk.Label(login_window, text="Vui lòng đăng nhập để điều khiển xe", bg=PANEL, fg=GRAY,
             font=FONT_SMALL).pack(pady=(2, 15))
    
    form_frame = tk.Frame(login_window, bg=PANEL, padx=40)
    form_frame.pack(fill="x")
    
    tk.Label(form_frame, text="TÊN ĐĂNG NHẬP", bg=PANEL, fg=GRAY3,
             font=FONT_SMALL, anchor="w").pack(fill="x", pady=(5, 2))
    username_entry = tk.Entry(form_frame, font=("Segoe UI", 11),
                               bg=PANEL2, fg=WHITE, relief="flat",
                               highlightthickness=1, highlightbackground=BORDER,
                               highlightcolor=CYAN, insertbackground=CYAN)
    username_entry.pack(fill="x", ipady=5, pady=(0, 8))
    username_entry.insert(0, "admin")
    username_entry.select_range(0, tk.END)
    username_entry.focus_set()
    
    tk.Label(form_frame, text="MẬT KHẨU", bg=PANEL, fg=GRAY3,
             font=FONT_SMALL, anchor="w").pack(fill="x", pady=(5, 2))
    password_entry = tk.Entry(form_frame, font=("Segoe UI", 11), show="•",
                               bg=PANEL2, fg=WHITE, relief="flat",
                               highlightthickness=1, highlightbackground=BORDER,
                               highlightcolor=CYAN, insertbackground=CYAN)
    password_entry.pack(fill="x", ipady=5, pady=(0, 15))
    password_entry.insert(0, "admin")
    
    error_label = tk.Label(login_window, text="", bg=PANEL, fg=RED,
                           font=FONT_SMALL)
    error_label.pack(pady=(0, 5))
    
    def attempt_login(event=None):
        user = username_entry.get().strip()
        pwd = password_entry.get().strip()
        
        if user == LOGIN_USER and pwd == LOGIN_PASS:
            login_window.destroy()
            root.deiconify()
            log("✅ Đăng nhập thành công. Chào mừng!", "info")
            show_toast("✅ Đăng nhập thành công!", "success", 2500)
        else:
            error_label.config(text="❌ Sai tên đăng nhập hoặc mật khẩu! Vui lòng nhập lại.")
            password_entry.delete(0, tk.END)
            password_entry.focus_set()
            form_frame.config(bg="#fff0f0")
            login_window.after(300, lambda: form_frame.config(bg=PANEL))
    
    def exit_app():
        if login_window:
            login_window.destroy()
        root.quit()
    
    btn_row = tk.Frame(login_window, bg=PANEL)
    btn_row.pack(pady=(8, 0))
    
    btn_login = tk.Button(btn_row, text="🔓 ĐĂNG NHẬP", command=attempt_login,
                          bg=CYAN, fg="white", font=FONT_MED,
                          relief="flat", cursor="hand2", padx=16, pady=8,
                          activebackground="#007299", activeforeground="white",
                          width=11)
    btn_login.pack(side="left", padx=4)
    
    btn_register = tk.Button(btn_row, text="📝 ĐĂNG KÝ", command=lambda: None,
                              bg=PANEL2, fg=CYAN, font=FONT_MED,
                              relief="flat", cursor="hand2", padx=16, pady=8,
                              activebackground=BTN_HOVER, activeforeground=WHITE,
                              width=11)
    btn_register.pack(side="left", padx=4)
    
    btn_exit = tk.Button(btn_row, text="🚪 THOÁT", command=exit_app,
                          bg=RED_DIM, fg=RED, font=FONT_MED,
                          relief="flat", cursor="hand2", padx=16, pady=8,
                          activebackground=RED, activeforeground="white",
                          width=11)
    btn_exit.pack(side="left", padx=4)
    
    tk.Label(login_window, text="(Mặc định: admin / admin)", bg=PANEL, fg=GRAY2,
             font=FONT_SMALL).pack(pady=(10, 5))
    
    username_entry.bind("<Return>", attempt_login)
    password_entry.bind("<Return>", attempt_login)



def connect():
    """Kết nối đến ESP32 qua TCP socket"""
    global sock
    ip   = ip_var.get().strip()
    port_str = port_var.get().strip()

    if not ip or not port_str:
        log("Nhập IP và Port trước!", "danger")
        return

    try:
        port = int(port_str)
    except ValueError:
        log("Port không hợp lệ!", "danger")
        return

    set_conn_status("connecting")
    root.update_idletasks()

    def do_connect():
        global sock
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((ip, port))
            s.settimeout(None)
            sock = s
            root.after(0, lambda: set_conn_status("connected", ip, port))
            root.after(0, lambda: log(f"Kết nối thành công → {ip}:{port}", "info"))
            t = threading.Thread(target=receive_loop, daemon=True)
            t.start()
        except Exception as e:
            root.after(0, lambda: set_conn_status("disconnected"))
            root.after(0, lambda: log(f"Lỗi kết nối: {e}", "danger"))

    threading.Thread(target=do_connect, daemon=True).start()


def disconnect():
    """Ngắt kết nối"""
    global sock
    if sock:
        try:
            sock.close()
        except:
            pass
        sock = None
    set_conn_status("disconnected")
    log("Đã ngắt kết nối.", "info")


def send(cmd):
    """Gửi lệnh ký tự đến ESP32"""
    global sock
    if sock:
        try:
            sock.sendall(cmd.encode())
        except Exception as e:
            log(f"Lỗi gửi lệnh '{cmd}': {e}", "danger")
            root.after(0, disconnect)
    else:
        log("Chưa kết nối với xe!", "danger")



def receive_loop():
    """Vòng lặp nhận dữ liệu chạy trong thread riêng"""
    buffer = ""
    while sock:
        try:
            data = sock.recv(1024).decode('utf-8', errors='ignore')
            if not data:
                break
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                if line.startswith("DIST:"):
                    val = line.split(":")[1]
                    root.after(0, update_distance, val)
                elif line == "WARN:obstacle":
                    root.after(0, on_obstacle_warning)
                elif line == "WARN:blocked":
                    root.after(0, on_blocked_warning)
                elif line == "WARN:crash":
                    root.after(0, lambda: log("💥 Va chạm phát hiện!", "danger"))
                elif line.startswith("AUTO:"):
                    state = line.split(":")[1]
                    root.after(0, lambda s=state: log(f"Safe Drive: {s}", "info"))
                elif line == "READY":
                    root.after(0, lambda: log("✅ ESP32 sẵn sàng!", "info"))
        except:
            break
    root.after(0, lambda: log("⚠️ Mất kết nối với xe!", "danger"))
    root.after(0, lambda: set_conn_status("disconnected"))


def on_obstacle_warning():
    """Khi ESP32 báo có vật cản và đã dừng xe"""
    log("🛑 VẬT CẢN! Xe đã dừng tự động.", "danger")
    dist_canvas.itemconfig(dist_arc, outline=RED)
    flash_warning()
    show_toast("⚠️ VẬT CẢN! Xe đã dừng tự động", "danger", 4000)


def on_blocked_warning():
    """Khi GUI gửi tiến nhưng bị chặn do safe mode"""
    log("🚫 Không thể tiến — có vật cản phía trước!", "danger")
    show_toast("🚫 Không thể tiến! Vật cản phía trước", "danger", 3000)


def flash_warning():
    """Nháy đỏ khu vực khoảng cách để cảnh báo"""
    dist_canvas.itemconfig(dist_arc, outline=RED)
    root.after(300, lambda: dist_canvas.itemconfig(dist_arc, outline=ORANGE))
    root.after(600, lambda: dist_canvas.itemconfig(dist_arc, outline=RED))
    root.after(900, lambda: dist_canvas.itemconfig(dist_arc, outline=ORANGE))



def update_distance(val):
    """Cập nhật hiển thị khoảng cách từ cảm biến"""
    global last_distance
    try:
        d = int(val)
        last_distance = d

        dist_value_label.config(text=f"{d}")

        if d <= 20:
            color = RED
            status = "NGUY HIỂM"
            status_icon = "🔴"
        elif d <= 40:
            color = ORANGE
            status = "CHÚ Ý"
            status_icon = "🟠"
        elif d < 999:
            color = GREEN
            status = "AN TOÀN"
            status_icon = "🟢"
        else:
            color = GRAY
            status = "---"
            status_icon = "⚪"

        dist_value_label.config(fg=color)
        dist_status_label.config(text=status, fg=color)
        dist_status_icon.config(text=status_icon)
        dist_canvas.itemconfig(dist_arc, outline=color)

        dist_metric_value.config(text=f"{d}", fg=color)
        dist_metric_status.config(text=status, fg=color)
        if d <= 20:
            dist_metric_box.config(bg="#fff0f0", highlightbackground=RED, highlightcolor=RED)
        elif d <= 40:
            dist_metric_box.config(bg="#fff5e6", highlightbackground=ORANGE, highlightcolor=ORANGE)
        elif d < 999:
            dist_metric_box.config(bg="#f0fff4", highlightbackground=GREEN, highlightcolor=GREEN)
        else:
            dist_metric_box.config(bg=PANEL2, highlightbackground=GRAY, highlightcolor=GRAY)

        pct = min(d, 200) / 200.0
        angle = int(pct * 270)
        dist_canvas.itemconfig(dist_arc, extent=-angle)

        if safe_mode_on and d <= 20:
            btn_forward.config(bg=RED_DIM, fg=RED)
        elif safe_mode_on:
            btn_forward.config(bg=PANEL2, fg=CYAN)

    except:
        dist_value_label.config(text="?")


def set_conn_status(state, ip="", port=""):
    """Cập nhật hiển thị trạng thái kết nối"""
    if state == "connected":
        conn_dot.config(bg=GREEN)
        conn_label.config(text=f"CONNECTED  {ip}:{port}", fg=GREEN)
        btn_connect.config(text="DISCONNECT", bg=RED_DIM, fg=RED,
                           command=disconnect)
        show_toast("✅ Đã kết nối với ESP32!", "success")
    elif state == "connecting":
        conn_dot.config(bg=ORANGE)
        conn_label.config(text="CONNECTING...", fg=ORANGE)
    else:
        conn_dot.config(bg=GRAY)
        conn_label.config(text="DISCONNECTED", fg=GRAY)
        btn_connect.config(text="CONNECT", bg=CYAN_DIM, fg=CYAN,
                           command=connect)


def update_clock():
    """Đồng hồ realtime ở tiêu đề"""
    clock_label.config(text=time.strftime("%H:%M:%S"))
    root.after(1000, update_clock)


def log(msg, tag="normal"):
    """Ghi vào log"""
    timestamp = time.strftime("%H:%M:%S")
    log_box.config(state='normal')
    log_box.insert(tk.END, f"[{timestamp}] {msg}\n", tag)
    log_box.see(tk.END)
    log_box.config(state='disabled')



def cmd_forward():
    """Tiến — bị chặn nếu safe mode và vật cản <= 20cm"""
    if safe_mode_on and last_distance <= 20 and last_distance > 0:
        log("🚫 Safe Drive: Không thể tiến! Vật cản phía trước.", "danger")
        flash_warning()
        show_toast("🚫 Safe Drive chặn: Vật cản phía trước!", "danger", 3000)
        return
    send('F')
    show_toast("⬆️ Tiến", "info", 800)


def cmd_backward():
    send('B')
    show_toast("⬇️ Lùi", "info", 800)


def cmd_left():
    send('L')
    show_toast("⬅️ Rẽ trái", "info", 800)


def cmd_right():
    send('R')
    show_toast("➡️ Rẽ phải", "info", 800)


def cmd_stop():
    send('S')
    show_toast("⏹ Dừng xe", "warning", 800)


def on_speed(val):
    """Gửi tốc độ khi kéo slider"""
    send(str(int(float(val))))


def toggle_headlight():
    """Bật/tắt đèn pha"""
    global headlight_on
    headlight_on = not headlight_on
    if headlight_on:
        send('H')
        btn_headlight.config(bg=YELLOW_DIM, fg=YELLOW, text="💡 ĐÈN PHA\n  ON")
        log("Đèn pha: BẬT", "info")
        show_toast("💡 Đèn pha BẬT", "success", 2000)
    else:
        send('h')
        btn_headlight.config(bg=PANEL2, fg=GRAY, text="💡 ĐÈN PHA\n  OFF")
        log("Đèn pha: TẮT", "info")
        show_toast("💡 Đèn pha TẮT", "warning", 2000)


def toggle_left_signal():
    """Bật/tắt xi nhan trái"""
    global left_signal_on
    left_signal_on = not left_signal_on
    if left_signal_on:
        send('Q')
        btn_left_sig.config(bg=YELLOW_DIM, fg=YELLOW, text="◀◀ XI NHAN\n  TRÁI")
        log("Xi nhan trái: BẬT", "info")
        show_toast("◀ Xi nhan trái BẬT", "success", 2000)
    else:
        send('q')
        btn_left_sig.config(bg=PANEL2, fg=GRAY, text="◀ XI NHAN\n  TRÁI")
        log("Xi nhan trái: TẮT", "info")
        show_toast("◀ Xi nhan trái TẮT", "warning", 2000)


def toggle_right_signal():
    """Bật/tắt xi nhan phải"""
    global right_signal_on
    right_signal_on = not right_signal_on
    if right_signal_on:
        send('E')
        btn_right_sig.config(bg=YELLOW_DIM, fg=YELLOW, text="XI NHAN ▶▶\n  PHẢI")
        log("Xi nhan phải: BẬT", "info")
        show_toast("▶ Xi nhan phải BẬT", "success", 2000)
    else:
        send('e')
        btn_right_sig.config(bg=PANEL2, fg=GRAY, text="XI NHAN ▶\n  PHẢI")
        log("Xi nhan phải: TẮT", "info")
        show_toast("▶ Xi nhan phải TẮT", "warning", 2000)


def toggle_horn():
    """Bật/tắt còi thường"""
    global horn_on
    horn_on = not horn_on
    if horn_on:
        send('Z')
        btn_horn.config(bg=ORANGE_DIM, fg=ORANGE, text="📢 CÒI\n  ON")
        log("Còi: BẬT", "info")
        show_toast("📢 Còi BẬT", "success", 2000)
    else:
        send('z')
        btn_horn.config(bg=PANEL2, fg=GRAY, text="📢 CÒI\n  OFF")
        log("Còi: TẮT", "info")
        show_toast("📢 Còi TẮT", "warning", 2000)


def toggle_police():
    """Bật/tắt còi cảnh sát"""
    global police_on, police_flash_id
    police_on = not police_on
    if police_on:
        send('P')
        btn_police.config(bg=PURPLE_DIM, fg=PURPLE, text="🚨 CẢNH SÁT\n  ON")
        log("Còi cảnh sát: BẬT", "info")
        show_toast("🚨 Còi cảnh sát BẬT", "success", 2500)
        police_flash_loop()
    else:
        send('p')
        btn_police.config(bg=PANEL2, fg=GRAY, text="🚨 CẢNH SÁT\n  OFF")
        log("Còi cảnh sát: TẮT", "info")
        show_toast("🚨 Còi cảnh sát TẮT", "warning", 2500)
        if police_flash_id:
            root.after_cancel(police_flash_id)
            police_flash_id = None
        title_bar.config(bg=PANEL)


def police_flash_loop():
    """Hiệu ứng nháy đỏ/xanh ở tiêu đề khi còi cảnh sát bật"""
    global police_flash_id
    if not police_on:
        return
    current = title_bar.cget("bg")
    next_color = "#e1bee7" if current == "#e3f2fd" else "#e3f2fd"
    title_bar.config(bg=next_color)
    police_flash_id = root.after(300, police_flash_loop)


def toggle_safe_mode():
    """Bật/tắt Safe Drive Mode"""
    global safe_mode_on
    safe_mode_on = not safe_mode_on
    if safe_mode_on:
        send('A')
        btn_safe.config(bg="#d4f5e0", fg=GREEN,
                        text="🛡️ SAFE DRIVE\n    ON",
                        relief="solid", bd=1)
        safe_indicator.config(bg=GREEN)
        log("🛡️ Safe Drive Mode: BẬT — Xe tự dừng khi vật cản ≤ 20cm", "info")
        show_toast("🛡️ Safe Drive Mode BẬT", "success", 3000)
    else:
        send('a')
        btn_safe.config(bg=PANEL2, fg=GRAY,
                        text="🛡️ SAFE DRIVE\n    OFF",
                        relief="flat", bd=0)
        safe_indicator.config(bg=GRAY2)
        btn_forward.config(bg=PANEL2, fg=CYAN)
        log("Safe Drive Mode: TẮT", "info")
        show_toast("🛡️ Safe Drive Mode TẮT", "warning", 3000)



def key_press(e):
    """Nhấn phím → gửi lệnh điều khiển"""
    key_map = {
        'w': cmd_forward,  'Up': cmd_forward,
        's': cmd_backward, 'Down': cmd_backward,
        'a': cmd_left,     'Left': cmd_left,
        'd': cmd_right,    'Right': cmd_right,
        'space': cmd_stop,
        'h': toggle_headlight,
        'z': toggle_horn,
    }
    fn = key_map.get(e.keysym.lower())
    if fn:
        fn()


def key_release(e):
    """Nhả phím di chuyển → dừng xe"""
    move_keys = {'w', 's', 'a', 'd', 'up', 'down', 'left', 'right'}
    if e.keysym.lower() in move_keys:
        send('S')



def make_button(parent, text, command, width=10, height=2,
                bg=None, fg=None, font=None):
    """Tạo nút với style mặc định và hiệu ứng hover"""
    bg   = bg   or PANEL2
    fg   = fg   or CYAN
    font = font or FONT_MED
    btn = tk.Button(
        parent, text=text, command=command,
        width=width, height=height,
        bg=bg, fg=fg, font=font,
        relief="flat", bd=0,
        activebackground=BTN_HOVER, activeforeground=WHITE,
        cursor="hand2",
        padx=4, pady=2
    )
    def on_enter(e, b=btn, orig_bg=bg):
        b.config(bg=BTN_HOVER)
    def on_leave(e, b=btn, orig_bg=bg):
        b.config(bg=orig_bg)
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn


def make_panel(parent, title="", padx=8, pady=8):
    """Tạo panel có viền và tiêu đề"""
    outer = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
    inner = tk.Frame(outer, bg=PANEL, padx=padx, pady=pady)
    inner.pack(fill="both", expand=True)
    if title:
        lbl = tk.Label(inner, text=title, bg=PANEL, fg=CYAN,
                       font=FONT_SMALL, anchor="w")
        lbl.pack(fill="x", pady=(0, 4))
        sep = tk.Frame(inner, bg=BORDER, height=1)
        sep.pack(fill="x", pady=(0, 6))
    return outer, inner


def make_metric_box(parent, label, unit="", bg=PANEL2):
    """Tạo metrics box nổi bật để hiển thị chỉ số"""
    frame = tk.Frame(parent, bg=bg, padx=10, pady=6,
                     highlightbackground=GRAY2, highlightthickness=1,
                     relief="flat")
    tk.Label(frame, text=label, bg=bg, fg=GRAY3,
             font=FONT_SMALL).pack(anchor="center")
    val_frame = tk.Frame(frame, bg=bg)
    val_frame.pack(pady=(2, 0))
    value_lbl = tk.Label(val_frame, text="---", bg=bg, fg=CYAN,
                         font=FONT_METRIC)
    value_lbl.pack(side="left")
    if unit:
        tk.Label(val_frame, text=unit, bg=bg, fg=GRAY,
                 font=FONT_BIG).pack(side="left", padx=(2, 0))
    status_lbl = tk.Label(frame, text="---", bg=bg, fg=GRAY,
                          font=FONT_SMALL)
    status_lbl.pack(anchor="center", pady=(0, 2))
    return frame, value_lbl, status_lbl


root = tk.Tk()
root.title("ESP32 CAR — CONTROL DASHBOARD")
root.geometry("780x880")
root.configure(bg=BG)
root.resizable(False, False)

toast_frame = tk.Frame(root, bg=PANEL, padx=8, pady=6)
toast_frame.place(relx=0.5, y=8, anchor="n")
toast_label = tk.Label(toast_frame, text="", bg=PANEL, fg=GRAY3,
                       font=FONT_MED, wraplength=400, padx=10, pady=4)
toast_label.pack()

title_bar = tk.Frame(root, bg=PANEL, pady=12)
title_bar.pack(fill="x", padx=0, pady=0)

title_icon = tk.Label(title_bar, text="🚗", bg=PANEL, fg=CYAN,
                      font=("Segoe UI", 22))
title_icon.pack(side="left", padx=(20, 4))

tk.Label(title_bar, text="ESP32 RC CAR", bg=PANEL, fg=CYAN,
         font=FONT_TITLE).pack(side="left")

ver_badge = tk.Label(title_bar, text="v3.0", bg=CYAN_DIM, fg=CYAN,
                     font=FONT_SMALL, padx=6, pady=1, relief="flat")
ver_badge.pack(side="left", padx=(8, 0))

tk.Label(title_bar, text="  SAFE:", bg=PANEL, fg=GRAY,
         font=FONT_SMALL).pack(side="left", padx=(20, 2))
safe_indicator = tk.Label(title_bar, text="●", bg=PANEL, fg=GRAY2,
                           font=FONT_BIG)
safe_indicator.pack(side="left")

conn_header_dot = tk.Label(title_bar, text="  ●", bg=PANEL, fg=GRAY,
                           font=FONT_BIG)
conn_header_dot.pack(side="left", padx=(12, 0))

clock_label = tk.Label(title_bar, text="", bg=PANEL, fg=GRAY,
                       font=("Segoe UI", 11, "bold"))
clock_label.pack(side="right", padx=20)

header_sep = tk.Frame(root, bg=CYAN, height=2)
header_sep.pack(fill="x")

main = tk.Frame(root, bg=BG)
main.pack(fill="both", expand=True, padx=10, pady=8)

col_left  = tk.Frame(main, bg=BG, width=360)
col_right = tk.Frame(main, bg=BG, width=380)
col_left.pack(side="left",  fill="both", expand=True, padx=(0, 5))
col_right.pack(side="right", fill="both", expand=True, padx=(5, 0))
col_left.pack_propagate(False)
col_right.pack_propagate(False)



p_outer, p_conn = make_panel(col_left, "  ⚡ CONNECTION")
p_outer.pack(fill="x", pady=(0, 6))

row_ip = tk.Frame(p_conn, bg=PANEL)
row_ip.pack(fill="x", pady=2)

tk.Label(row_ip, text="IP", bg=PANEL, fg=GRAY, font=FONT_SMALL,
         width=3).pack(side="left")
ip_var = tk.StringVar(value="10.118.79.42")
tk.Entry(row_ip, textvariable=ip_var, width=16,
         bg=PANEL2, fg=CYAN, insertbackground=CYAN,
         relief="flat", font=FONT_MONO,
         highlightthickness=1, highlightbackground=BORDER,
         highlightcolor=CYAN).pack(side="left", padx=4)

tk.Label(row_ip, text="PORT", bg=PANEL, fg=GRAY,
         font=FONT_SMALL).pack(side="left", padx=(6, 2))
port_var = tk.StringVar(value="8888")
tk.Entry(row_ip, textvariable=port_var, width=6,
         bg=PANEL2, fg=CYAN, insertbackground=CYAN,
         relief="flat", font=FONT_MONO,
         highlightthickness=1, highlightbackground=BORDER,
         highlightcolor=CYAN).pack(side="left", padx=4)

btn_connect = tk.Button(
    row_ip, text="CONNECT", command=connect,
    bg=CYAN_DIM, fg=CYAN, font=FONT_MED,
    relief="flat", padx=10, pady=3, cursor="hand2",
    activebackground=BTN_HOVER, activeforeground=WHITE
)
btn_connect.pack(side="left", padx=6)

row_status = tk.Frame(p_conn, bg=PANEL)
row_status.pack(fill="x", pady=(2, 0))
conn_dot   = tk.Label(row_status, text=" ●", bg=PANEL, fg=GRAY,
                      font=FONT_BIG)
conn_dot.pack(side="left")
conn_label = tk.Label(row_status, text="DISCONNECTED", bg=PANEL, fg=GRAY,
                      font=FONT_SMALL)
conn_label.pack(side="left", padx=4)


p_outer2, p_ctrl = make_panel(col_left, "  🎮 MOVEMENT CONTROL")
p_outer2.pack(fill="x", pady=6)

ctrl_grid = tk.Frame(p_ctrl, bg=PANEL)
ctrl_grid.pack(pady=6)

btn_forward = make_button(ctrl_grid, "▲\nTIẾN", cmd_forward,
                           width=9, height=2, fg=CYAN)
btn_forward.grid(row=0, column=1, padx=4, pady=4)

make_button(ctrl_grid, "◀  TRÁI", cmd_left,
            width=9, height=2, fg=CYAN).grid(row=1, column=0, padx=4, pady=4)

btn_stop = tk.Button(
    ctrl_grid, text="■\nDỪNG", command=cmd_stop,
    width=9, height=2,
    bg=RED_DIM, fg=RED, font=FONT_BIG,
    relief="flat", cursor="hand2",
    activebackground=RED, activeforeground=WHITE
)
btn_stop.grid(row=1, column=1, padx=4, pady=4)

make_button(ctrl_grid, "PHẢI  ▶", cmd_right,
            width=9, height=2, fg=CYAN).grid(row=1, column=2, padx=4, pady=4)

make_button(ctrl_grid, "▼\nLÙI", cmd_backward,
            width=9, height=2, fg=CYAN).grid(row=2, column=1, padx=4, pady=4)

tk.Label(p_ctrl, text="[ WASD / Arrow Keys = Move   Space = Stop ]",
         bg=PANEL, fg=GRAY, font=FONT_SMALL).pack(pady=(0, 4))


p_outer3, p_speed = make_panel(col_left, "  ⚙️ SPEED CONTROL")
p_outer3.pack(fill="x", pady=6)

speed_row = tk.Frame(p_speed, bg=PANEL)
speed_row.pack(fill="x", pady=4)

tk.Label(speed_row, text="MIN", bg=PANEL, fg=GRAY,
         font=FONT_SMALL).pack(side="left", padx=(4, 0))

speed_var = tk.IntVar(value=7)
spd_scale = tk.Scale(
    speed_row, from_=1, to=9, orient="horizontal",
    variable=speed_var, command=on_speed,
    length=200, bg=PANEL, fg=CYAN,
    highlightthickness=0, troughcolor=BORDER,
    sliderrelief="flat", activebackground=CYAN,
    showvalue=False
)
spd_scale.pack(side="left", padx=6)

tk.Label(speed_row, text="MAX", bg=PANEL, fg=GRAY,
         font=FONT_SMALL).pack(side="left")

speed_display = tk.Label(speed_row, textvariable=speed_var,
                          bg=PANEL, fg=CYAN, font=FONT_BIG, width=2)
speed_display.pack(side="left", padx=8)

speed_levels = tk.Frame(p_speed, bg=PANEL)
speed_levels.pack(fill="x", pady=(0, 4))
for i in range(9):
    level = tk.Frame(speed_levels, bg=CYAN_DIM if i < 7 else GRAY2,
                     width=28, height=4, relief="flat")
    level.pack(side="left", padx=1)


p_outer4, p_safe = make_panel(col_left, "  🛡️ SAFE DRIVE MODE")
p_outer4.pack(fill="x", pady=6)

safe_row = tk.Frame(p_safe, bg=PANEL)
safe_row.pack(fill="x", pady=4)

btn_safe = tk.Button(
    safe_row, text="🛡️ SAFE DRIVE\n    OFF",
    command=toggle_safe_mode,
    width=14, height=2,
    bg=PANEL2, fg=GRAY, font=FONT_MED,
    relief="flat", cursor="hand2",
    activebackground=BTN_HOVER, activeforeground=WHITE
)
btn_safe.pack(side="left", padx=4, pady=4)

safe_info_text = """Tự động dừng khi vật cản
≤ 20cm kèm cảnh báo"""
tk.Label(safe_row,
         text=safe_info_text,
         bg=PANEL, fg=GRAY, font=FONT_SMALL,
         justify="left").pack(side="left", padx=12)



p_outer5, p_dist = make_panel(col_right, "  📡 DISTANCE SENSOR")
p_outer5.pack(fill="x", pady=(0, 6))

metrics_row = tk.Frame(p_dist, bg=PANEL)
metrics_row.pack(fill="x", pady=(4, 2))

dist_metric_box, dist_metric_value, dist_metric_status = make_metric_box(
    metrics_row, "KHOẢNG CÁCH", "cm", PANEL3
)
dist_metric_box.pack(side="left", fill="x", expand=True, padx=(0, 3))

status_metric_frame = tk.Frame(metrics_row, bg=PANEL3, padx=8, pady=6,
                               highlightbackground=GRAY2, highlightthickness=1,
                               relief="flat")
tk.Label(status_metric_frame, text="TRẠNG THÁI", bg=PANEL3, fg=GRAY3,
         font=FONT_SMALL).pack(anchor="center")
dist_status_icon = tk.Label(status_metric_frame, text="⚪", bg=PANEL3,
                            font=("Segoe UI", 20))
dist_status_icon.pack(pady=(2, 0))
dist_status_label = tk.Label(status_metric_frame, text="---", bg=PANEL3, fg=GRAY,
                             font=FONT_BIG)
dist_status_label.pack(anchor="center")
status_metric_frame.pack(side="left", fill="x", expand=True, padx=(3, 0))

sensor_row = tk.Frame(p_dist, bg=PANEL)
sensor_row.pack(fill="x", pady=4)

dist_canvas = tk.Canvas(sensor_row, width=110, height=110,
                         bg=PANEL, highlightthickness=0)
dist_canvas.pack(side="left", padx=4, pady=4)

dist_canvas.create_arc(10, 10, 100, 100,
                        start=-225, extent=270,
                        style="arc", outline=GRAY2, width=6)
dist_arc = dist_canvas.create_arc(10, 10, 100, 100,
                                   start=-225, extent=0,
                                   style="arc", outline=GREEN, width=6)

dist_value_label = tk.Label(dist_canvas, text="---",
                              bg=PANEL, fg=GREEN,
                              font=("Segoe UI", 18, "bold"))
dist_canvas.create_window(55, 48, window=dist_value_label)
dist_canvas.create_text(55, 73, text="cm", fill=GRAY, font=FONT_SMALL)

dist_info = tk.Frame(sensor_row, bg=PANEL)
dist_info.pack(side="left", fill="both", expand=True, pady=4, padx=(8, 0))

tk.Label(dist_info, text="CẢNH BÁO", bg=PANEL, fg=CYAN,
         font=FONT_SMALL).pack(anchor="w")

warn_items = [
    ("≤ 20cm  →  DỪNG KHẨN", RED),
    ("≤ 40cm  →  CHÚ Ý", ORANGE),
    ("> 40cm  →  AN TOÀN", GREEN),
]
for text, color in warn_items:
    row = tk.Frame(dist_info, bg=PANEL)
    row.pack(fill="x", pady=1)
    dot = tk.Label(row, text="●", bg=PANEL, fg=color, font=FONT_SMALL)
    dot.pack(side="left", padx=(0, 4))
    tk.Label(row, text=text, bg=PANEL, fg=GRAY,
             font=FONT_SMALL).pack(side="left", anchor="w")


p_outer6, p_lights = make_panel(col_right, "  💡 LIGHTS")
p_outer6.pack(fill="x", pady=6)

lights_row = tk.Frame(p_lights, bg=PANEL)
lights_row.pack(fill="x", pady=6)

btn_headlight = tk.Button(
    lights_row, text="💡 ĐÈN PHA\n  OFF",
    command=toggle_headlight,
    width=11, height=2,
    bg=PANEL2, fg=GRAY, font=FONT_MED,
    relief="flat", cursor="hand2",
    activebackground=BTN_HOVER, activeforeground=WHITE
)
btn_headlight.pack(side="left", padx=3)

btn_left_sig = tk.Button(
    lights_row, text="◀ XI NHAN\n  TRÁI",
    command=toggle_left_signal,
    width=11, height=2,
    bg=PANEL2, fg=GRAY, font=FONT_MED,
    relief="flat", cursor="hand2",
    activebackground=BTN_HOVER, activeforeground=WHITE
)
btn_left_sig.pack(side="left", padx=3)

btn_right_sig = tk.Button(
    lights_row, text="XI NHAN ▶\n  PHẢI",
    command=toggle_right_signal,
    width=11, height=2,
    bg=PANEL2, fg=GRAY, font=FONT_MED,
    relief="flat", cursor="hand2",
    activebackground=BTN_HOVER, activeforeground=WHITE
)
btn_right_sig.pack(side="left", padx=3)


p_outer7, p_horn = make_panel(col_right, "  📢 HORN & SIREN")
p_outer7.pack(fill="x", pady=6)

horn_row = tk.Frame(p_horn, bg=PANEL)
horn_row.pack(fill="x", pady=6)

btn_horn = tk.Button(
    horn_row, text="📢 CÒI\n  OFF",
    command=toggle_horn,
    width=11, height=2,
    bg=PANEL2, fg=GRAY, font=FONT_MED,
    relief="flat", cursor="hand2",
    activebackground=BTN_HOVER, activeforeground=WHITE
)
btn_horn.pack(side="left", padx=3)

btn_police = tk.Button(
    horn_row, text="🚨 CẢNH SÁT\n  OFF",
    command=toggle_police,
    width=13, height=2,
    bg=PANEL2, fg=GRAY, font=FONT_MED,
    relief="flat", cursor="hand2",
    activebackground=BTN_HOVER, activeforeground=WHITE
)
btn_police.pack(side="left", padx=3)

tk.Label(p_horn,
         text="Còi cảnh sát nháy đèn LED trái/phải trên xe",
         bg=PANEL, fg=GRAY2, font=FONT_SMALL).pack(anchor="w", pady=(0, 2))


p_outer8, p_log = make_panel(col_right, "  📋 SYSTEM LOG")
p_outer8.pack(fill="both", expand=True, pady=(6, 0))

log_box = scrolledtext.ScrolledText(
    p_log, height=8, state='disabled',
    bg="#f5f6fa", fg=GRAY3,
    font=FONT_MONO, relief="flat",
    insertbackground=CYAN,
    selectbackground=CYAN_DIM,
    padx=4, pady=4
)
log_box.pack(fill="both", expand=True)
log_box.tag_config("danger", foreground=RED)
log_box.tag_config("info",   foreground="#006699")
log_box.tag_config("normal", foreground=GRAY3)

clear_log_frame = tk.Frame(p_log, bg=PANEL)
clear_log_frame.pack(fill="x", pady=(4, 2))
tk.Button(
    clear_log_frame, text="🗑 CLEAR LOG", command=lambda: (
        log_box.config(state='normal'),
        log_box.delete('1.0', tk.END),
        log_box.config(state='disabled')
    ),
    bg=PANEL2, fg=GRAY, font=FONT_SMALL,
    relief="flat", cursor="hand2", pady=2, padx=8
).pack(side="right")


tk.Frame(root, bg=CYAN, height=2).pack(fill="x")
status_bar = tk.Frame(root, bg=PANEL, pady=6)
status_bar.pack(fill="x")
tk.Label(status_bar,
         text="  ◈ ESP32 RC Car Control Dashboard  |  v3.0  |  Python + tkinter",
         bg=PANEL, fg=GRAY, font=FONT_SMALL).pack(side="left")
tk.Label(status_bar,
         text="[ H=Đèn pha | Z=Còi | WASD=Di chuyển | Space=Dừng ]  ",
         bg=PANEL, fg=GRAY2, font=FONT_SMALL).pack(side="right")


root.bind("<KeyPress>",   key_press)
root.bind("<KeyRelease>", key_release)

root.withdraw()
root.after(100, show_login_window)

update_clock()
log("Hệ thống khởi động. Nhập IP và nhấn CONNECT.", "info")
log("Phím tắt: WASD/Arrow=Di chuyển  H=Đèn  Z=Còi  Space=Dừng", "normal")

root.mainloop()