#include <WiFi.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <ArduinoJson.h>

// --- Edge Node Configuration ---
const char* ssid = "YOUR_LOCAL_WIFI_SSID";
const char* password = "YOUR_LOCAL_WIFI_PASSWORD";
const char* portalAuthUrl = "http://YOUR_PORTAL_IP:3000/edge-auth";

// The hardcoded secret for this specific device
const String deviceId = "ESP32_NODE_01";
const String hardwareSecret = "YOUR_DEVICE_SECRET";

// NVS Storage object
Preferences preferences;
String localJWT = "";

void authenticateWithPortal();

void setup() {
  Serial.begin(115200);
  
  // 1. Connect to Local Sovereign Network
  WiFi.begin(ssid, password);
  Serial.print("Connecting to Local Network...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to Sovereign Network.");

  // 2. Open NVS and check for an existing token
  preferences.begin("auth", false);
  localJWT = preferences.getString("jwt", "");

  // 3. If no token exists, or if it's blank, request a new one
  if (localJWT == "") {
    Serial.println("No JWT found in NVS. Requesting new token from Blue-Moon-Portal...");
    authenticateWithPortal();
  } else {
    Serial.println("JWT loaded from NVS. Ready to transmit data.");
  }
}

void loop() {
  // Your sensor reading logic goes here...
  
  // Example of deep sleep to save battery
  // ESP.deepSleep(10e6); // Sleep for 10 seconds, then reboot
}

void authenticateWithPortal() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(portalAuthUrl);
    http.addHeader("Content-Type", "application/json");

    // Build the JSON payload
    StaticJsonDocument<200> doc;
    doc["deviceId"] = deviceId;
    doc["hardwareSecret"] = hardwareSecret;
    
    String requestBody;
    serializeJson(doc, requestBody);

    // POST to the portal
    int httpResponseCode = http.POST(requestBody);

    if (httpResponseCode == 200) {
      String response = http.getString();
      
      // Parse the incoming JWT
      StaticJsonDocument<512> responseDoc;
      deserializeJson(responseDoc, response);
      const char* token = responseDoc["accessToken"];
      
      // Save it to global variable and NVS so it survives reboots
      localJWT = String(token);
      preferences.putString("jwt", localJWT);
      
      Serial.println("Authentication successful. JWT saved to secure storage.");
    } else {
      Serial.print("Auth failed. HTTP Response code: ");
      Serial.println(httpResponseCode);
    }
    
    http.end();
  }
}
