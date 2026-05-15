/*
 * ============================================================
 *   ESP32 RC Car – Firmware v3
 *   Motor Driver : TB6612FNG
 *   Sensor       : HC-SR04
 *   Communication: WiFi TCP port 8888
 * ============================================================
 *  THAY ĐỔI SO VỚI v2:
 *  - Thêm "Safe Drive Mode" (lệnh 'A'/'a') — chặn tiến khi vật cản <= 20cm
 *    và phát còi cảnh báo liên tục
 *  - Thêm "Police Siren" (lệnh 'P'/'p') — còi hú kiểu cảnh sát + nháy đèn
 *  - Còi thường vẫn dùng 'Z'/'z' như cũ
 *  - Safe Drive Mode không ảnh hưởng đến: đèn, xi nhan, còi thường, còi cảnh sát
 *  - Tất cả chân PIN giữ nguyên so với v2
 * ============================================================
 *  BẢNG LỆNH (gửi từ Python GUI):
 *    F = Tiến         B = Lùi
 *    L = Rẽ trái      R = Rẽ phải      S = Dừng
 *    H = Đèn pha ON   h = Đèn pha OFF
 *    Q = Xi nhan T ON q = Xi nhan T OFF
 *    E = Xi nhan P ON e = Xi nhan P OFF
 *    Z = Còi ON       z = Còi OFF
 *    P = Còi cảnh sát ON   p = Còi cảnh sát OFF
 *    A = Safe Drive ON     a = Safe Drive OFF
 *    0-9 = Tốc độ
 *
 *  DỮ LIỆU GỬI VỀ GUI:
 *    DIST:<cm>        — khoảng cách cảm biến
 *    WARN:obstacle    — vật cản <= 20cm (safe mode)
 *    AUTO:ON / AUTO:OFF
 *    ACK:<cmd>        — xác nhận lệnh
 *    READY            — sẵn sàng
 * ============================================================
 */

#include <WiFi.h>

// ── WiFi ─────────────────────────────────────────────────────
const char* ssid     = "nguyen";       // <-- Đổi tên WiFi của bạn
const char* password = "123456789";    // <-- Đổi mật khẩu WiFi

WiFiServer server(8888);
WiFiClient client;

// ── PIN MOTOR (TB6612FNG) ─────────────────────────────────────
#define AIN1  27
#define AIN2  14
#define PWMA  25
#define BIN1  12
#define BIN2  13
#define PWMB  26
#define STBY  33

// ── PIN LED ───────────────────────────────────────────────────
#define LED_FRONT  2    // Đèn pha trước
#define LED_LEFT   16   // Xi nhan trái
#define LED_RIGHT  17   // Xi nhan phải

// ── PIN BUZZER ────────────────────────────────────────────────
#define BUZZER  22

// ── PIN SENSOR (HC-SR04) ──────────────────────────────────────
#define TRIG_PIN  5
#define ECHO_PIN  18

// ── PWM CHANNELS ─────────────────────────────────────────────
#define PWM_FREQ  1000
#define PWM_RES   8
#define CH_A      0     // Motor A
#define CH_B      1     // Motor B
#define CH_BUZZ   2     // Buzzer

// ── BIẾN TRẠNG THÁI ──────────────────────────────────────────
int  currentSpeed  = 200;   // PWM tốc độ (50–255)
bool safeDriveMode = false;  // Chế độ lái an toàn
bool policeSiren   = false;  // Còi cảnh sát đang bật
bool hornOn        = false;  // Còi thường đang bật
bool guiConnected  = false;

// ── BIẾN TIMING (non-blocking) ────────────────────────────────
unsigned long lastSendTime      = 0;
unsigned long lastWaitPrint     = 0;
unsigned long lastSirenToggle   = 0;  // Còi cảnh sát nháy
unsigned long lastWarnBeep      = 0;  // Beep cảnh báo an toàn
unsigned long warnBeepEnd       = 0;  // Khi nào hết cảnh báo

bool sirenHighFreq   = true;  // Trạng thái tần số còi cảnh sát
bool sirenLedState   = false; // Trạng thái nháy đèn còi cảnh sát
bool warnBeepState   = false; // Trạng thái beep cảnh báo
bool isWarning       = false; // Đang trong trạng thái cảnh báo

// Tần số còi cảnh sát: xen kẽ giữa 2 tần số
const int SIREN_FREQ_HIGH = 1800;
const int SIREN_FREQ_LOW  = 1000;
const int SIREN_INTERVAL  = 400;   // ms mỗi nửa chu kỳ

// Cảnh báo vật cản: beep nhanh
const int WARN_BEEP_FREQ  = 2500;
const int WARN_BEEP_INT   = 200;   // ms mỗi beep


// ════════════════════════════════════════════════════════════
//   SETUP
// ════════════════════════════════════════════════════════════
void setup() {
  Serial.begin(115200);

  // Motor pins
  pinMode(AIN1, OUTPUT); pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT); pinMode(BIN2, OUTPUT);
  pinMode(STBY, OUTPUT);
  digitalWrite(STBY, LOW);  // Tắt driver cho đến khi GUI kết nối

  // PWM motor
  ledcSetup(CH_A, PWM_FREQ, PWM_RES);
  ledcSetup(CH_B, PWM_FREQ, PWM_RES);
  ledcAttachPin(PWMA, CH_A);
  ledcAttachPin(PWMB, CH_B);

  // PWM buzzer
  ledcSetup(CH_BUZZ, 2000, PWM_RES);
  ledcAttachPin(BUZZER, CH_BUZZ);
  ledcWrite(CH_BUZZ, 0);

  // LED
  pinMode(LED_FRONT, OUTPUT); digitalWrite(LED_FRONT, LOW);
  pinMode(LED_LEFT,  OUTPUT); digitalWrite(LED_LEFT,  LOW);
  pinMode(LED_RIGHT, OUTPUT); digitalWrite(LED_RIGHT, LOW);

  // Sensor
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  stopCar();

  // Kết nối WiFi
  Serial.print("Dang ket noi WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi da ket noi!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  server.begin();
  Serial.println(">>> Dang cho GUI ket noi...");
}


// ════════════════════════════════════════════════════════════
//   MOTOR FUNCTIONS
// ════════════════════════════════════════════════════════════
void setMotor(int spd) {
  ledcWrite(CH_A, abs(spd));
  ledcWrite(CH_B, abs(spd));
}

void forward() {
  digitalWrite(STBY, HIGH);
  digitalWrite(AIN1, HIGH); digitalWrite(AIN2, LOW);
  digitalWrite(BIN1, LOW);  digitalWrite(BIN2, HIGH); // Motor B đối xứng
  setMotor(currentSpeed);
}

void backward() {
  digitalWrite(STBY, HIGH);
  digitalWrite(AIN1, LOW);  digitalWrite(AIN2, HIGH);
  digitalWrite(BIN1, HIGH); digitalWrite(BIN2, LOW);
  setMotor(currentSpeed);
}

void turnLeft() {
  digitalWrite(STBY, HIGH);
  digitalWrite(AIN1, LOW);  digitalWrite(AIN2, HIGH); // Bánh trái lùi
  digitalWrite(BIN1, LOW);  digitalWrite(BIN2, HIGH); // Bánh phải tiến
  setMotor(currentSpeed);
}

void turnRight() {
  digitalWrite(STBY, HIGH);
  digitalWrite(AIN1, HIGH); digitalWrite(AIN2, LOW);  // Bánh trái tiến
  digitalWrite(BIN1, HIGH); digitalWrite(BIN2, LOW);  // Bánh phải lùi
  setMotor(currentSpeed);
}

void stopCar() {
  ledcWrite(CH_A, 0);
  ledcWrite(CH_B, 0);
  digitalWrite(AIN1, LOW); digitalWrite(AIN2, LOW);
  digitalWrite(BIN1, LOW); digitalWrite(BIN2, LOW);
}

void resetAll() {
  stopCar();
  digitalWrite(STBY, LOW);
  digitalWrite(LED_FRONT, LOW);
  digitalWrite(LED_LEFT,  LOW);
  digitalWrite(LED_RIGHT, LOW);
  // Chỉ tắt buzzer nếu không phải còi thường do user bật
  ledcWrite(CH_BUZZ, 0);
  hornOn       = false;
  policeSiren  = false;
  safeDriveMode = false;
  isWarning    = false;
}


// ════════════════════════════════════════════════════════════
//   BUZZER FUNCTIONS
// ════════════════════════════════════════════════════════════

// Còi thường ON/OFF — do user điều khiển
void hornTurnOn() {
  hornOn = true;
  // Chỉ bật buzzer nếu không có cảnh báo hay siren đang chạy
  if (!policeSiren && !isWarning) {
    ledcSetup(CH_BUZZ, 2000, PWM_RES);
    ledcWrite(CH_BUZZ, 128);
  }
}
void hornTurnOff() {
  hornOn = false;
  // Nếu không có gì khác đang dùng buzzer thì tắt
  if (!policeSiren && !isWarning) {
    ledcWrite(CH_BUZZ, 0);
  }
}

// Cập nhật buzzer mỗi loop (non-blocking)
void updateBuzzer(unsigned long now) {

  // ── Cảnh báo vật cản (ưu tiên cao nhất) ──
  if (isWarning) {
    if (now - lastWarnBeep >= WARN_BEEP_INT) {
      lastWarnBeep = now;
      warnBeepState = !warnBeepState;
      if (warnBeepState) {
        ledcSetup(CH_BUZZ, WARN_BEEP_FREQ, PWM_RES);
        ledcWrite(CH_BUZZ, 200); // Gần tối đa
      } else {
        ledcWrite(CH_BUZZ, 0);
      }
    }
    return; // Không để siren hay horn đè lên
  }

  // ── Còi cảnh sát ──
  if (policeSiren) {
    if (now - lastSirenToggle >= SIREN_INTERVAL) {
      lastSirenToggle = now;
      sirenHighFreq = !sirenHighFreq;
      sirenLedState = !sirenLedState;

      // Đổi tần số
      int freq = sirenHighFreq ? SIREN_FREQ_HIGH : SIREN_FREQ_LOW;
      ledcSetup(CH_BUZZ, freq, PWM_RES);
      ledcWrite(CH_BUZZ, 160);

      // Nháy đèn trái/phải xen kẽ
      digitalWrite(LED_LEFT,  sirenLedState ? HIGH : LOW);
      digitalWrite(LED_RIGHT, sirenLedState ? LOW  : HIGH);
    }
    return;
  }

  // ── Còi thường ──
  if (hornOn) {
    // Buzzer đã được bật trong hornTurnOn(), không cần làm thêm
    return;
  }

  // Không có gì đang bật → tắt buzzer
  ledcWrite(CH_BUZZ, 0);
}


// ════════════════════════════════════════════════════════════
//   SENSOR
// ════════════════════════════════════════════════════════════
long getDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long dur = pulseIn(ECHO_PIN, HIGH, 15000);
  if (dur == 0) return 999;
  return dur * 0.034 / 2;
}


// ════════════════════════════════════════════════════════════
//   GỬI DỮ LIỆU VỀ GUI
// ════════════════════════════════════════════════════════════
void sendData(String msg) {
  if (client && client.connected()) {
    client.println(msg);
  }
  Serial.println(msg);
}


// ════════════════════════════════════════════════════════════
//   XỬ LÝ LỆNH TỪ GUI
// ════════════════════════════════════════════════════════════
void handleCommand(char cmd) {
  Serial.print("CMD: "); Serial.println(cmd);

  switch (cmd) {

    // ── Di chuyển ──────────────────────────────────────────
    case 'F':
      // Safe Drive Mode: chặn tiến nếu vật cản <= 20cm
      if (safeDriveMode) {
        long d = getDistance();
        if (d > 0 && d <= 20) {
          sendData("WARN:blocked");  // Thông báo GUI bị chặn
          isWarning = true;
          return;
        }
      }
      isWarning = false;
      forward();
      sendData("ACK:F");
      break;

    case 'B':
      backward();
      sendData("ACK:B");
      break;

    case 'L':
      turnLeft();
      sendData("ACK:L");
      break;

    case 'R':
      turnRight();
      sendData("ACK:R");
      break;

    case 'S':
      stopCar();
      isWarning = false;
      sendData("ACK:S");
      break;

    // ── Tốc độ 0–9 → map sang 50–255 ──────────────────────
    case '0': case '1': case '2': case '3': case '4':
    case '5': case '6': case '7': case '8': case '9':
      currentSpeed = map(cmd - '0', 0, 9, 50, 255);
      sendData("ACK:SPEED_" + String(currentSpeed));
      break;

    // ── Đèn pha ────────────────────────────────────────────
    case 'H': digitalWrite(LED_FRONT, HIGH); sendData("ACK:H"); break;
    case 'h': digitalWrite(LED_FRONT, LOW);  sendData("ACK:h"); break;

    // ── Xi nhan ────────────────────────────────────────────
    case 'Q':
      // Nếu còi cảnh sát đang dùng đèn trái thì vẫn cho xi nhan
      if (!policeSiren) digitalWrite(LED_LEFT, HIGH);
      sendData("ACK:Q");
      break;
    case 'q':
      if (!policeSiren) digitalWrite(LED_LEFT, LOW);
      sendData("ACK:q");
      break;
    case 'E':
      if (!policeSiren) digitalWrite(LED_RIGHT, HIGH);
      sendData("ACK:E");
      break;
    case 'e':
      if (!policeSiren) digitalWrite(LED_RIGHT, LOW);
      sendData("ACK:e");
      break;

    // ── Còi thường ─────────────────────────────────────────
    case 'Z': hornTurnOn();  sendData("ACK:Z"); break;
    case 'z': hornTurnOff(); sendData("ACK:z"); break;

    // ── Còi cảnh sát ───────────────────────────────────────
    case 'P':
      policeSiren = true;
      lastSirenToggle = 0; // Reset để bắt đầu ngay
      sendData("ACK:P");
      break;
    case 'p':
      policeSiren = false;
      // Tắt đèn xi nhan (nếu còi cảnh sát đã nháy)
      digitalWrite(LED_LEFT,  LOW);
      digitalWrite(LED_RIGHT, LOW);
      // Khôi phục còi thường nếu đang bật
      if (hornOn) {
        ledcSetup(CH_BUZZ, 2000, PWM_RES);
        ledcWrite(CH_BUZZ, 128);
      } else {
        ledcWrite(CH_BUZZ, 0);
      }
      sendData("ACK:p");
      break;

    // ── Safe Drive Mode ────────────────────────────────────
    case 'A':
      safeDriveMode = true;
      sendData("AUTO:ON");
      break;
    case 'a':
      safeDriveMode = false;
      isWarning = false;
      sendData("AUTO:OFF");
      break;
  }
}


// ════════════════════════════════════════════════════════════
//   LOOP CHÍNH
// ════════════════════════════════════════════════════════════
void loop() {

  // ── Chờ GUI kết nối ──────────────────────────────────────
  if (!guiConnected) {
    if (millis() - lastWaitPrint >= 2000) {
      lastWaitPrint = millis();
      Serial.print(">>> Dang cho GUI... | IP: ");
      Serial.println(WiFi.localIP());
    }
    client = server.available();
    if (client) {
      guiConnected = true;
      Serial.println(">>> GUI da ket noi! He thong BAT DAU!");
      sendData("READY");
      digitalWrite(STBY, HIGH);
    }
    return;
  }

  // ── GUI ngắt kết nối ─────────────────────────────────────
  if (!client || !client.connected()) {
    guiConnected = false;
    resetAll();
    Serial.println(">>> GUI ngat ket noi! Cho GUI moi...");
    return;
  }

  unsigned long now = millis();

  // ── Nhận và xử lý lệnh từ GUI ────────────────────────────
  while (client.available()) {
    char cmd = client.read();
    handleCommand(cmd);
  }

  // ── Đọc sensor & gửi về GUI mỗi 300ms ───────────────────
  if (now - lastSendTime >= 300) {
    lastSendTime = now;
    long dist = getDistance();
    sendData("DIST:" + String(dist));

    // Safe Drive Mode: phát hiện vật cản gần
    if (safeDriveMode && dist > 0 && dist <= 20) {
      stopCar();
      isWarning = true;
      sendData("WARN:obstacle");
    } else if (safeDriveMode && dist > 20) {
      // Hết vật cản, tắt cảnh báo
      if (isWarning) {
        isWarning = false;
        // Khôi phục trạng thái buzzer
        if (hornOn) {
          ledcSetup(CH_BUZZ, 2000, PWM_RES);
          ledcWrite(CH_BUZZ, 128);
        }
      }
    }
  }

  // ── Cập nhật buzzer (non-blocking) ───────────────────────
  updateBuzzer(now);
}
