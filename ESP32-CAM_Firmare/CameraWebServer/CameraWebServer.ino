#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <WiFiClient.h>

// ===========================
// Select camera model
// ===========================
#include "board_config.h"

// ===========================
// WiFi credentials
// ===========================
const char *ssid = "JazJaz 2.4";
const char *password = "6f0fad0bad";

// ===========================
// CONFIGURACIÓN IP FIJA
// ===========================
IPAddress local_IP(192, 168, 100, 15);  // Cambia esta IP por cámara
IPAddress gateway(192, 168, 100, 1);
IPAddress subnet(255, 255, 255, 0);
// IPAddress primaryDNS(8, 8, 8, 8);    // Opcional
// IPAddress secondaryDNS(8, 8, 4, 4);  // Opcional

// Declarar el server como global
WebServer server(80);

void startCameraServer();
void setupLedFlash();

// Variables para estadísticas
unsigned long lastUpdate = 0;
int personCount = 0;

// Endpoints adicionales para cam_ip_system
void handleStatus() {
  String json = "{";
  json += "\"status\":\"RUNNING\"";
  json += ",\"personas\":" + String(personCount);
  json += ",\"ultima_actualizacion\":\"" + String(millis()) + "\"";
  json += ",\"timestamp\":\"" + String(millis()) + "\"";
  json += "}";
  server.send(200, "application/json", json);
}

void handleStats() {
  String json = "{";
  json += "\"estado\":\"RUNNING\"";
  json += ",\"personas_detectadas\":" + String(personCount);
  json += ",\"ultima_actualizacion\":\"" + String(millis()) + "\"";
  json += "}";
  server.send(200, "application/json", json);
}

void handlePing() {
  server.send(200, "text/plain", "OK");
}

void handleStream() {
  server.sendHeader("Location", "/stream");
  server.send(302, "text/plain", "Redirecting to stream");
}

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  // ===========================
  // CONFIGURAR IP FIJA
  // ===========================
  if (!WiFi.config(local_IP, gateway, subnet)) {
    Serial.println("Error al configurar IP fija!");
  }

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_UXGA;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  if (config.pixel_format == PIXFORMAT_JPEG) {
    if (psramFound()) {
      config.jpeg_quality = 10;
      config.fb_count = 2;
      config.grab_mode = CAMERA_GRAB_LATEST;
    } else {
      config.frame_size = FRAMESIZE_SVGA;
      config.fb_location = CAMERA_FB_IN_DRAM;
    }
  } else {
    config.frame_size = FRAMESIZE_240X240;
#if CONFIG_IDF_TARGET_ESP32S3
    config.fb_count = 2;
#endif
  }

#if defined(CAMERA_MODEL_ESP_EYE)
  pinMode(13, INPUT_PULLUP);
  pinMode(14, INPUT_PULLUP);
#endif

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);
    s->set_brightness(s, 1);
    s->set_saturation(s, -2);
  }
  if (config.pixel_format == PIXFORMAT_JPEG) {
    s->set_framesize(s, FRAMESIZE_QVGA);
  }

#if defined(CAMERA_MODEL_M5STACK_WIDE) || defined(CAMERA_MODEL_M5STACK_ESP32CAM)
  s->set_vflip(s, 1);
  s->set_hmirror(s, 1);
#endif

#if defined(CAMERA_MODEL_ESP32S3_EYE)
  s->set_vflip(s, 1);
#endif

#if defined(LED_GPIO_NUM)
  setupLedFlash();
#endif

  WiFi.begin(ssid, password);
  WiFi.setSleep(false);

  Serial.print("WiFi connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  
  // Mostrar IP asignada
  Serial.print("Camera IP: ");
  Serial.println(WiFi.localIP());

  // Configurar endpoints adicionales
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/stats", HTTP_GET, handleStats);
  server.on("/ping", HTTP_GET, handlePing);
  server.on("/stream", HTTP_GET, handleStream);

  startCameraServer();

  Serial.print("Camera Ready! Use 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("' to connect");
  Serial.println("Endpoints disponibles:");
  Serial.println("  /status - Estado de la cámara");
  Serial.println("  /stats  - Estadísticas");
  Serial.println("  /ping   - Test de conexión");
}

void loop() {
  if (millis() - lastUpdate > 30000) {
    lastUpdate = millis();
    personCount = 0;
  }
  
  server.handleClient();
  delay(2);
}