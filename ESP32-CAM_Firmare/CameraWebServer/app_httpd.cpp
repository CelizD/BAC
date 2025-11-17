// Copyright 2015-2016 Espressif Systems (Shanghai) PTE LTD
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
#include "esp_http_server.h"
#include "esp_timer.h"
#include "esp_camera.h"
#include "img_converters.h"
#include "fb_gfx.h"
#include "esp32-hal-ledc.h"
#include "sdkconfig.h"
#include "camera_index.h"
#include "board_config.h"

#if defined(ARDUINO_ARCH_ESP32) && defined(CONFIG_ARDUHAL_ESP_LOG)
#include "esp32-hal-log.h"
#endif

// LED FLASH setup
#if defined(LED_GPIO_NUM)
#define CONFIG_LED_MAX_INTENSITY 255

int led_duty = 0;
bool isStreaming = false;

#endif

typedef struct {
  httpd_req_t *req;
  size_t len;
} jpg_chunking_t;

#define PART_BOUNDARY "123456789000000000000987654321"
static const char *_STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char *_STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char *_STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\nX-Timestamp: %d.%06d\r\n\r\n";

httpd_handle_t stream_httpd = NULL;
httpd_handle_t camera_httpd = NULL;

typedef struct {
  size_t size;   //number of values used for filtering
  size_t index;  //current value index
  size_t count;  //value count
  int sum;
  int *values;  //array to be filled with values
} ra_filter_t;

static ra_filter_t ra_filter;

static ra_filter_t *ra_filter_init(ra_filter_t *filter, size_t sample_size) {
  memset(filter, 0, sizeof(ra_filter_t));

  filter->values = (int *)malloc(sample_size * sizeof(int));
  if (!filter->values) {
    return NULL;
  }
  memset(filter->values, 0, sample_size * sizeof(int));

  filter->size = sample_size;
  return filter;
}

#if ARDUHAL_LOG_LEVEL >= ARDUHAL_LOG_LEVEL_INFO
static int ra_filter_run(ra_filter_t *filter, int value) {
  if (!filter->values) {
    return value;
  }
  filter->sum -= filter->values[filter->index];
  filter->values[filter->index] = value;
  filter->sum += filter->values[filter->index];
  filter->index++;
  filter->index = filter->index % filter->size;
  if (filter->count < filter->size) {
    filter->count++;
  }
  return filter->sum / filter->count;
}
#endif

#if defined(LED_GPIO_NUM)
void enable_led(bool en) {  // Turn LED On or Off
  int duty = en ? led_duty : 0;
  if (en && isStreaming && (led_duty > CONFIG_LED_MAX_INTENSITY)) {
    duty = CONFIG_LED_MAX_INTENSITY;
  }
  ledcWrite(LED_GPIO_NUM, duty);
  log_i("Set LED intensity to %d", duty);
}
#endif

// =============================================
// SISTEMA DE AUTENTICACIÓN SIMPLE Y ESTABLE
// =============================================

// Credenciales
const char* AUTH_USER = "admin";
const char* AUTH_PASS = "admin123";

// Macro MIN para el error de compilación
#ifndef MIN
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#endif

// Función para verificar autenticación básica HTTP
static bool check_basic_auth(httpd_req_t *req) {
    size_t auth_len = httpd_req_get_hdr_value_len(req, "Authorization");
    if (auth_len == 0) {
        return false;
    }
    
    // Verificar longitud máxima razonable
    if (auth_len > 200) {
        return false;
    }
    
    char *auth_header = (char *)malloc(auth_len + 1);
    if (!auth_header) {
        log_e("Failed to allocate memory for auth header");
        return false;
    }
    
    // Inicializar memoria
    memset(auth_header, 0, auth_len + 1);
    
    esp_err_t ret = httpd_req_get_hdr_value_str(req, "Authorization", auth_header, auth_len + 1);
    if (ret != ESP_OK) {
        log_e("Failed to get auth header: %d", ret);
        free(auth_header);
        return false;
    }
    
    bool authenticated = false;
    
    // Verificar que el header comienza con "Basic " y tiene longitud razonable
    if (strncmp(auth_header, "Basic ", 6) == 0 && strlen(auth_header) > 6) {
        const char* encoded = auth_header + 6;
        // Verificación simple - comparar con el base64 conocido
        if (strcmp(encoded, "YWRtaW46YWRtaW4xMjM=") == 0) { // admin:admin123 en base64
            authenticated = true;
            log_i("Authentication successful");
        } else {
            log_i("Authentication failed - invalid credentials");
        }
    } else {
        log_i("Invalid Authorization header format");
    }
    
    free(auth_header);
    return authenticated;
}

// Middleware de autenticación simple
static bool check_auth(httpd_req_t *req) {
    // Para endpoints públicos, permitir acceso sin autenticación
    const char* uri = req->uri;
    if (strstr(uri, "/api/") == uri) {
        return true;  // APIs públicas para tu Django
    }
    
    // Para endpoints protegidos, verificar Basic Auth
    if (check_basic_auth(req)) {
        return true;
    }
    
    // Si no está autenticado, enviar header de autenticación
    httpd_resp_set_status(req, "401 Unauthorized");
    httpd_resp_set_hdr(req, "WWW-Authenticate", "Basic realm=\"ESP32-CAM\"");
    httpd_resp_send(req, NULL, 0);
    return false;
}

// =============================================
// HANDLERS PROTEGIDOS
// =============================================

static esp_err_t index_handler_protected(httpd_req_t *req) {
    if (!check_auth(req)) return ESP_OK;
    return index_handler(req);
}

static esp_err_t stream_handler_protected(httpd_req_t *req) {
    if (!check_auth(req)) return ESP_OK;
    return stream_handler(req);
}

static esp_err_t status_handler_protected(httpd_req_t *req) {
    if (!check_auth(req)) return ESP_OK;
    return status_handler(req);
}

static esp_err_t cmd_handler_protected(httpd_req_t *req) {
    if (!check_auth(req)) return ESP_OK;
    return cmd_handler(req);
}

static esp_err_t capture_handler_protected(httpd_req_t *req) {
    if (!check_auth(req)) return ESP_OK;
    return capture_handler(req);
}

// =============================================
// HANDLERS PÚBLICOS PARA DJANGO
// =============================================

static esp_err_t cam_ip_status_handler(httpd_req_t *req) {
    char json_response[256];
    unsigned long current_time = esp_timer_get_time() / 1000;
    
    snprintf(json_response, sizeof(json_response), 
             "{\"status\":\"RUNNING\",\"model\":\"ESP32-CAM\",\"timestamp\":\"%lu\"}",
             current_time);
    
    httpd_resp_set_type(req, "application/json");
    return httpd_resp_send(req, json_response, strlen(json_response));
}

static esp_err_t cam_ip_ping_handler(httpd_req_t *req) {
    httpd_resp_set_type(req, "text/plain");
    return httpd_resp_send(req, "OK", 2);
}

// ... (el resto de los handlers se mantienen igual - bmp_handler, capture_handler, etc.)

void startCameraServer() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.max_uri_handlers = 20;

    // Endpoints protegidos (requieren autenticación)
    httpd_uri_t index_uri = {
        .uri = "/", .method = HTTP_GET, .handler = index_handler_protected, .user_ctx = NULL
    };
    httpd_uri_t stream_uri = {
        .uri = "/stream", .method = HTTP_GET, .handler = stream_handler_protected, .user_ctx = NULL
    };
    httpd_uri_t capture_uri = {
        .uri = "/capture", .method = HTTP_GET, .handler = capture_handler_protected, .user_ctx = NULL
    };
    httpd_uri_t status_uri = {
        .uri = "/status", .method = HTTP_GET, .handler = status_handler_protected, .user_ctx = NULL
    };

    // Endpoints públicos para Django
    httpd_uri_t cam_ip_status_uri = {
        .uri = "/api/status", .method = HTTP_GET, .handler = cam_ip_status_handler, .user_ctx = NULL
    };
    httpd_uri_t cam_ip_ping_uri = {
        .uri = "/api/ping", .method = HTTP_GET, .handler = cam_ip_ping_handler, .user_ctx = NULL
    };

    ra_filter_init(&ra_filter, 20);

    log_i("Starting web server on port: '%d'", config.server_port);
    if (httpd_start(&camera_httpd, &config) == ESP_OK) {
        // Registrar endpoints protegidos
        httpd_register_uri_handler(camera_httpd, &index_uri);
        httpd_register_uri_handler(camera_httpd, &stream_uri);
        httpd_register_uri_handler(camera_httpd, &capture_uri);
        httpd_register_uri_handler(camera_httpd, &status_uri);
        
        // Registrar endpoints públicos para Django
        httpd_register_uri_handler(camera_httpd, &cam_ip_status_uri);
        httpd_register_uri_handler(camera_httpd, &cam_ip_ping_uri);
    }

    config.server_port += 1;
    config.ctrl_port += 1;
    log_i("Starting stream server on port: '%d'", config.server_port);
    if (httpd_start(&stream_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(stream_httpd, &stream_uri);
    }
}