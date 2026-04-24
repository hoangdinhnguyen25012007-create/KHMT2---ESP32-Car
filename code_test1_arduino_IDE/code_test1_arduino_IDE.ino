#include <WiFi.h>
#include <WiFiServer.h>

// ===== WIFI CONFIG =====
const char* ssid     = "nguyen";      // ← ĐỔI TÊN WIFI NHÀ BẠN
const char* password = "123456789";   // ← ĐỔI MẬT KHẨU

WiFiServer server(8888);
WiFiClient client;

// ===== PIN MOTOR =====
#define AIN1  26
#define AIN2  27
#define PWMA  25
#define BIN1  12
#define BIN2  13
#define PWMB  14
#define STBY  33

// ===== PIN LED =====
#define LED_FRONT  23     // ← ĐÃ ĐỔI TỪ 2 sang 23 (đèn pha thật)
#define LED_LEFT   16
#define LED_RIGHT  17

// ===== PIN BUZZER =====
#define BUZZER  15

// ===== PIN SENSOR =====
#define TRIG  4
#define ECHO  18
#define VIB   35

// ===== PWM CONFIG =====
#define PWM_FREQ  1000
#define PWM_RES   8
#define CH_A      0
#define CH_B      1
#define CH_BUZZ   2

int currentSpeed = 200;
bool autoStop = true;
unsigned long lastSendTime = 0;
unsigned long buzzerOffTime = 0;
bool buzzerAuto = false;

// ===== SETUP =====
void setup() {
  Serial.begin(115200);

  // Motor
  pinMode(AIN1, OUTPUT); pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT); pinMode(BIN2, OUTPUT);
  pinMode(STBY, OUTPUT);
  digitalWrite(STBY, HIGH);

  // PWM motor + buzzer
  ledcSetup(CH_A, PWM_FREQ, PWM_RES);
  ledcSetup(CH_B, PWM_FREQ, PWM_RES);
  ledcSetup(CH_BUZZ, 2000, PWM_RES);
  ledcAttachPin(PWMA, CH_A);
  ledcAttachPin(PWMB, CH_B);
  ledcAttachPin(BUZZER, CH_BUZZ);

  // LED
  pinMode(LED_FRONT, OUTPUT);
  pinMode(LED_LEFT,  OUTPUT);
  pinMode(LED_RIGHT, OUTPUT);
  digitalWrite(LED_FRONT, LOW);
  digitalWrite(LED_LEFT,  LOW);
  digitalWrite(LED_RIGHT, LOW);

  // Sensor HC-SR04
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  digitalWrite(TRIG, LOW);        // ← Đảm bảo Trig bắt đầu LOW

  pinMode(VIB, INPUT);

  stopCar();

  // Kết nối WiFi
  Serial.print("Đang kết nối WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ WiFi đã kết nối!");
  Serial.print("📡 IP ESP32: ");
  Serial.println(WiFi.localIP());

  server.begin();
  Serial.println("🚗 Server TCP sẵn sàng - Chờ GUI kết nối...");
}

// ===== HÀM MOTOR =====
void setMotor(int speedA, int speedB) {
  ledcWrite(CH_A, abs(speedA));
  ledcWrite(CH_B, abs(speedB));
}

void forward()  { digitalWrite(AIN1, HIGH); digitalWrite(AIN2, LOW);
                  digitalWrite(BIN1, HIGH); digitalWrite(BIN2, LOW);
                  setMotor(currentSpeed, currentSpeed); }

void backward() { digitalWrite(AIN1, LOW);  digitalWrite(AIN2, HIGH);
                  digitalWrite(BIN1, LOW);  digitalWrite(BIN2, HIGH);
                  setMotor(currentSpeed, currentSpeed); }

void turnLeft() { digitalWrite(AIN1, LOW);  digitalWrite(AIN2, HIGH);
                  digitalWrite(BIN1, HIGH); digitalWrite(BIN2, LOW);
                  setMotor(currentSpeed, currentSpeed); }

void turnRight(){ digitalWrite(AIN1, HIGH); digitalWrite(AIN2, LOW);
                  digitalWrite(BIN1, LOW);  digitalWrite(BIN2, HIGH);
                  setMotor(currentSpeed, currentSpeed); }

void stopCar()  { digitalWrite(AIN1, LOW); digitalWrite(AIN2, LOW);
                  digitalWrite(BIN1, LOW); digitalWrite(BIN2, LOW);
                  setMotor(0, 0); }

// ===== BUZZER =====
void buzzerOn()  { ledcWrite(CH_BUZZ, 128); }
void buzzerOff() { ledcWrite(CH_BUZZ, 0); }

// ===== CẢM BIẾN HC-SR04 - ĐÃ FIX =====
long getDistance() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);

  // Tăng timeout lên 40000µs (~6.8 mét) + lọc giá trị
  long duration = pulseIn(ECHO, HIGH, 40000);

  if (duration == 0) return 999;                    // Không nhận echo
  long distance = duration * 0.034 / 2;

  // Lọc giá trị không thực tế
  if (distance < 2 || distance > 400) return 999;

  return distance;
}

// ===== GỬI DỮ LIỆU VỀ GUI =====
void sendData(String msg) {
  if (client && client.connected()) {
    client.println(msg);
  }
}

// ===== LOOP =====
void loop() {
  // Chấp nhận client mới
  if (!client || !client.connected()) {
    client = server.available();
    if (client) {
      Serial.println("✅ GUI đã kết nối!");
    }
    return;
  }

  // Nhận lệnh từ GUI
  while (client.available()) {
    char cmd = client.read();
    Serial.print("CMD: "); Serial.println(cmd);

    switch (cmd) {
      case 'F': forward();    break;
      case 'B': backward();   break;
      case 'L': turnLeft();   break;
      case 'R': turnRight();  break;
      case 'S': stopCar();    break;

      // Tốc độ 1-9
      case '0': case '1': case '2': case '3': case '4':
      case '5': case '6': case '7': case '8': case '9':
        currentSpeed = map(cmd - '0', 0, 9, 50, 255);
        break;

      // Đèn
      case 'H': digitalWrite(LED_FRONT, HIGH); sendData("HEADLIGHT:ON");  break;
      case 'h': digitalWrite(LED_FRONT, LOW);  sendData("HEADLIGHT:OFF"); break;
      case 'Q': digitalWrite(LED_LEFT,  HIGH); break;
      case 'q': digitalWrite(LED_LEFT,  LOW);  break;
      case 'E': digitalWrite(LED_RIGHT, HIGH); break;
      case 'e': digitalWrite(LED_RIGHT, LOW);  break;

      // Còi
      case 'Z': buzzerOn(); break;
      case 'z': buzzerOff(); break;

      // CÒI BÁO ĐỘNG (nút mới trong GUI)
      case 'X': buzzerOn();  sendData("ALARM:ON");  Serial.println("🚨 Còi báo động ON");  break;
      case 'x': buzzerOff(); sendData("ALARM:OFF"); Serial.println("🚨 Còi báo động OFF"); break;

      case 'A': autoStop = true;  sendData("AUTO:ON");  break;
      case 'a': autoStop = false; sendData("AUTO:OFF"); break;
    }
  }

  // Gửi khoảng cách + kiểm tra cảm biến mỗi 300ms
  unsigned long now = millis();
  if (now - lastSendTime >= 300) {
    lastSendTime = now;

    long dist = getDistance();
    sendData("DIST:" + String(dist));

    if (autoStop && dist < 20 && dist > 0) {
      stopCar();
      buzzerOn();
      sendData("WARN:obstacle");
      buzzerAuto = true;
      buzzerOffTime = now + 1000;
    }

    if (digitalRead(VIB) == HIGH) {
      sendData("WARN:crash");
      buzzerOn();
      buzzerAuto = true;
      buzzerOffTime = now + 500;
    }
  }

  // Tự tắt còi
  if (buzzerAuto && millis() > buzzerOffTime) {
    buzzerOff();
    buzzerAuto = false;
  }
}