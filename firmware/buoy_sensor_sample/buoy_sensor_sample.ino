#include <OneWire.h>
#include <DallasTemperature.h>
#include <SoftwareSerial.h>
#include <avr/pgmspace.h>

#define ONE_WIRE_BUS 2
#define USE_FAKE_GPS 1
#define ENABLE_DEBUG_LOGS 1

// SIM800L serial pins on Arduino Nano
#define GSM_RX_PIN 7
#define GSM_TX_PIN 8

// Reserved channels for future expansion
#define GPS_RX_PIN 4
#define GPS_TX_PIN 5
#define BATTERY_ANALOG_PIN A0

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);
SoftwareSerial gsm(GSM_RX_PIN, GSM_TX_PIN);

// Replace these placeholders with real values before field use.
const char APN[] PROGMEM = "YOUR_APN";
const char USER[] PROGMEM = "YOUR_APN_USER";
const char PASS[] PROGMEM = "YOUR_APN_PASSWORD";
const char URL[] PROGMEM = "https://your-api-url.example/telemetry";

const char DEVICE_ID[] PROGMEM = "YOUR_DEVICE_ID";
const char DEVICE_NAME[] PROGMEM = "YOUR_DEVICE_NAME";
const char TOKEN[] PROGMEM = "YOUR_DEVICE_TOKEN";

// Example fallback location used when a real GPS module is not present.
const float FAKE_LATITUDE = -22.943306;
const float FAKE_LONGITUDE = -43.073889;

const unsigned long SEND_INTERVAL_MS = 300000UL;
const long GSM_BAUD_RATE = 9600;

float readTemperature();
float readBatteryVoltage();
bool initModem();
bool initGPRS();
bool sendTelemetry(float temperature, float batteryVoltage);
bool sendAT(const String &cmd, const String &expected, unsigned long timeout);
bool waitForExpectedAT(
  const char *cmd,
  const char *expected,
  unsigned long timeout,
  uint8_t attempts,
  unsigned long retryDelayMs
);
String readResponse(unsigned long timeout);
void clearGsmBuffer();
void copyProgmemString(const char *source, char *destination, size_t destinationSize);
void logLine(const __FlashStringHelper *message);
void logValue(const __FlashStringHelper *label, const char *value);

void setup() {
  Serial.begin(9600);
  Serial.println(F("Booting buoy telemetry sample..."));
  delay(500);

  logLine(F("Starting buoy telemetry sample..."));
  logLine(F("Waiting 10 seconds for SIM800L boot..."));

  gsm.begin(GSM_BAUD_RATE);
  delay(10000);

  sensors.begin();

  if (!initModem()) {
    logLine(F("SIM800L did not answer to AT."));
    return;
  }

  if (!initGPRS()) {
    logLine(F("GPRS setup failed. Telemetry may not be sent."));
  }
}

void loop() {
  float temperature = readTemperature();
  float batteryVoltage = readBatteryVoltage();

  char temperatureLog[12];
  char batteryLog[12];

  dtostrf(temperature, 0, 2, temperatureLog);
  dtostrf(batteryVoltage, 0, 2, batteryLog);

  logValue(F("Temperature"), temperatureLog);
  logValue(F("Battery voltage"), batteryLog);

  if (!sendAT("AT", "OK", 2000)) {
    logLine(F("SIM800L stopped responding. Skipping this cycle."));
    delay(SEND_INTERVAL_MS);
    return;
  }

  if (sendTelemetry(temperature, batteryVoltage)) {
    logLine(F("Telemetry POST sent successfully."));
  } else {
    logLine(F("Telemetry POST failed."));
  }

  delay(SEND_INTERVAL_MS);
}

float readTemperature() {
  sensors.requestTemperatures();
  float value = sensors.getTempCByIndex(0);

  if (value == DEVICE_DISCONNECTED_C) {
    logLine(F("Temperature sensor disconnected."));
    return -999.0;
  }

  return value;
}

float readBatteryVoltage() {
  // Placeholder implementation.
  // Replace with real analog conversion logic if a battery divider is connected.
  (void)BATTERY_ANALOG_PIN;
  return 12.0;
}

bool initModem() {
  char baudBuffer[12];
  ltoa(GSM_BAUD_RATE, baudBuffer, 10);
  logValue(F("GSM baud"), baudBuffer);
  clearGsmBuffer();

  for (int attempt = 1; attempt <= 5; attempt++) {
    char attemptBuffer[4];
    itoa(attempt, attemptBuffer, 10);
    logValue(F("AT attempt"), attemptBuffer);

    if (sendAT("AT", "OK", 2000)) {
      logLine(F("SIM800L responded to AT."));
      sendAT("ATE0", "OK", 2000);
      return true;
    }

    delay(800);
  }

  return false;
}

bool initGPRS() {
  char apn[32];
  char user[24];
  char pass[24];
  String response;

  copyProgmemString(APN, apn, sizeof(apn));
  copyProgmemString(USER, user, sizeof(user));
  copyProgmemString(PASS, pass, sizeof(pass));

  logLine(F("Initializing GPRS..."));

  if (!sendAT("AT", "OK", 3000)) {
    logLine(F("SIM800L did not respond to AT."));
    return false;
  }

  sendAT("ATE0", "OK", 2000);

  gsm.println(F("AT+CPIN?"));
  response = readResponse(3000);
  logValue(F("SIM status"), response.c_str());
  if (response.indexOf("READY") == -1) {
    logLine(F("SIM card is not ready. Check PIN or chip contact."));
    return false;
  }

  gsm.println(F("AT+CSQ"));
  response = readResponse(3000);
  logValue(F("Signal"), response.c_str());

  gsm.println(F("AT+CREG?"));
  response = readResponse(3000);
  logValue(F("Network reg"), response.c_str());

  gsm.println(F("AT+CGREG?"));
  response = readResponse(3000);
  logValue(F("GPRS reg"), response.c_str());

  sendAT("AT+SAPBR=0,1", "OK", 5000);

  if (!waitForExpectedAT("AT+CGATT=1", "OK", 10000, 3, 3000)) {
    logLine(F("Failed to attach to the GPRS service."));
    return false;
  }

  if (!sendAT("AT+SAPBR=3,1,\"Contype\",\"GPRS\"", "OK", 3000)) {
    logLine(F("Failed to configure bearer connection type."));
    return false;
  }

  if (!sendAT(String("AT+SAPBR=3,1,\"APN\",\"") + apn + "\"", "OK", 3000)) {
    logLine(F("Failed to configure APN."));
    return false;
  }

  if (!sendAT(String("AT+SAPBR=3,1,\"USER\",\"") + user + "\"", "OK", 3000)) {
    logLine(F("Failed to configure APN user."));
    return false;
  }

  if (!sendAT(String("AT+SAPBR=3,1,\"PWD\",\"") + pass + "\"", "OK", 3000)) {
    logLine(F("Failed to configure APN password."));
    return false;
  }

  if (!sendAT("AT+SAPBR=1,1", "OK", 15000)) {
    logLine(F("Failed to open GPRS bearer."));
    return false;
  }

  if (!sendAT("AT+SAPBR=2,1", "+SAPBR: 1,1", 5000)) {
    logLine(F("GPRS bearer did not report as connected."));
    return false;
  }

  logLine(F("GPRS initialization finished."));
  return true;
}

bool sendTelemetry(float temperature, float batteryVoltage) {
  char tempBuffer[12];
  char batteryBuffer[12];
  char latitudeBuffer[16];
  char longitudeBuffer[16];
  char deviceId[32];
  char deviceName[48];
  char token[48];
  char url[128];
  char json[256];
  char urlCmd[180];
  char dataCmd[32];

  copyProgmemString(DEVICE_ID, deviceId, sizeof(deviceId));
  copyProgmemString(DEVICE_NAME, deviceName, sizeof(deviceName));
  copyProgmemString(TOKEN, token, sizeof(token));
  copyProgmemString(URL, url, sizeof(url));

  dtostrf(temperature, 0, 2, tempBuffer);
  dtostrf(batteryVoltage, 0, 2, batteryBuffer);

#if USE_FAKE_GPS
  dtostrf(FAKE_LATITUDE, 0, 6, latitudeBuffer);
  dtostrf(FAKE_LONGITUDE, 0, 6, longitudeBuffer);
#endif

  snprintf(
    json,
    sizeof(json),
#if USE_FAKE_GPS
    "{\"device_id\":\"%s\",\"device_name\":\"%s\",\"token\":\"%s\",\"temperature\":%s,\"battery_voltage\":%s,\"latitude\":%s,\"longitude\":%s}",
    deviceId,
    deviceName,
    token,
    tempBuffer,
    batteryBuffer,
    latitudeBuffer,
    longitudeBuffer
#else
    "{\"device_id\":\"%s\",\"device_name\":\"%s\",\"token\":\"%s\",\"temperature\":%s,\"battery_voltage\":%s}",
    deviceId,
    deviceName,
    token,
    tempBuffer,
    batteryBuffer
#endif
  );

  logValue(F("Payload"), json);

  sendAT("AT+HTTPTERM", "OK", 2000);

  if (!sendAT("AT+HTTPINIT", "OK", 5000)) {
    logLine(F("HTTPINIT failed. The bearer may be down or the HTTP service is unavailable."));
    return false;
  }

  if (!sendAT("AT+HTTPPARA=\"CID\",1", "OK", 3000)) {
    logLine(F("Failed to bind HTTP service to bearer 1."));
    sendAT("AT+HTTPTERM", "OK", 2000);
    return false;
  }

  if (!sendAT("AT+HTTPSSL=1", "OK", 3000)) {
    logLine(F("This SIM800L firmware did not accept HTTPSSL=1."));
    sendAT("AT+HTTPTERM", "OK", 2000);
    return false;
  }

  if (!sendAT("AT+HTTPPARA=\"CONTENT\",\"application/json\"", "OK", 3000)) {
    logLine(F("Failed to configure HTTP content type."));
    sendAT("AT+HTTPTERM", "OK", 2000);
    return false;
  }

  snprintf(urlCmd, sizeof(urlCmd), "AT+HTTPPARA=\"URL\",\"%s\"", url);
  if (!sendAT(urlCmd, "OK", 5000)) {
    logLine(F("Failed to configure the HTTP URL."));
    sendAT("AT+HTTPTERM", "OK", 2000);
    return false;
  }

  snprintf(dataCmd, sizeof(dataCmd), "AT+HTTPDATA=%u,10000", strlen(json));
  if (!sendAT(dataCmd, "DOWNLOAD", 5000)) {
    sendAT("AT+HTTPTERM", "OK", 2000);
    return false;
  }

  gsm.print(json);
  delay(5000);

  gsm.println("AT+HTTPACTION=1");

  String response = readResponse(15000);
  logValue(F("HTTPACTION response"), response.c_str());
  bool success = response.indexOf("+HTTPACTION: 1,200") != -1 ||
                 response.indexOf("+HTTPACTION:1,200") != -1;

  sendAT("AT+HTTPTERM", "OK", 3000);
  return success;
}

bool sendAT(const String &cmd, const String &expected, unsigned long timeout) {
  clearGsmBuffer();
  logValue(F(">>"), cmd.c_str());
  gsm.println(cmd);
  String response = readResponse(timeout);
  logValue(F("<<"), response.c_str());
  return response.indexOf(expected) != -1;
}

bool waitForExpectedAT(
  const char *cmd,
  const char *expected,
  unsigned long timeout,
  uint8_t attempts,
  unsigned long retryDelayMs
) {
  for (uint8_t attempt = 1; attempt <= attempts; attempt++) {
    if (sendAT(String(cmd), String(expected), timeout)) {
      return true;
    }

    if (attempt < attempts) {
      char attemptBuffer[4];
      itoa(attempt + 1, attemptBuffer, 10);
      logValue(F("Retry"), attemptBuffer);
      delay(retryDelayMs);
    }
  }

  return false;
}

String readResponse(unsigned long timeout) {
  unsigned long start = millis();
  String response = "";

  while (millis() - start < timeout) {
    while (gsm.available()) {
      response += (char)gsm.read();
    }
  }

  return response;
}

void clearGsmBuffer() {
  while (gsm.available()) {
    gsm.read();
  }
}

void copyProgmemString(const char *source, char *destination, size_t destinationSize) {
  strncpy_P(destination, source, destinationSize - 1);
  destination[destinationSize - 1] = '\0';
}

void logLine(const __FlashStringHelper *message) {
#if ENABLE_DEBUG_LOGS
  Serial.println(message);
#endif
}

void logValue(const __FlashStringHelper *label, const char *value) {
#if ENABLE_DEBUG_LOGS
  Serial.print(label);
  Serial.print(F(": "));
  Serial.println(value);
#endif
}
