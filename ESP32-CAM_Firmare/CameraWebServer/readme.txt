dispositivo usado: ESP32-CAM

- estandar ONVIF (proximamente)
- Compatibilidad CORS 

- abrir Arduino IDE y cambiar las credenciales de tu wifi del .ino:

// ==============================
// Enter your WiFi credentials //
// ==============================
const char *ssid = "**********";
const char *password = "**********";

- confirurar IP por modulo:


// ===========================
// CONFIGURACIÓN IP FIJA
// ===========================
IPAddress local_IP(192, 168, 100, 15);  // Cambia esta IP por cámara extra (16, 17, etc)
IPAddress gateway(192, 168, 100, 1);  //cambiar el gateway por el de tu modem
IPAddress subnet(255, 255, 255, 0);

- credenciales fijas de la camara (proximamente)

Usuario: admin

Contraseña: admin123

si quieres cambiar usuario y pass abres el app_httpd.cpp:

// =============================================
// SISTEMA DE AUTENTICACIÓN SIMPLE Y ESTABLE
// =============================================

// Credenciales
const char* AUTH_USER = "admin";
const char* AUTH_PASS = "admin123";


También deberías actualizar la verificación Basic Auth: (proximamente)

if (strcmp(encoded, "YWRtaW46YWRtaW4xMjM=") == 0) { // admin:admin123 en base64
Y cámbiala por el nuevo valor en base64. Puedes generar el nuevo base64

Usando Python:

import base64
print(base64.b64encode(b"tu_nuevo_usuario:tu_nueva_contraseña").decode())

Si quieres hacerlo más fácil, puedes comentar la verificación base64:

// Comentar esta verificación específica y confiar solo en la verificación normal
// if (strcmp(encoded, "YWRtaW46YWRtaW4xMjM=") == 0) {
//     authenticated = true;
// }