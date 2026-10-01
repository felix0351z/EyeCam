// obstacle_ble.ino - ESP32-C3, BLE-Peripheral for vibration motor
// Library "NimBLE-Arduino" (h2zero), API-Version 2.x
// Board: ESP32C3 Dev Module

#include <NimBLEDevice.h>

#define GPIO_MOTOR 4 

static const char *RIGHT_MOTOR = "OBSTACLE-R"; // "OBSTACLE-L"

#define SVC_UUID "12345678-1234-1234-1234-1234567890ac"
#define CHR_UUID "12345678-1234-1234-1234-1234567890ac"

class MotorCallbacks : public NimBLECharacteristicCallbacks {
void onWrite(NimBLECharacteristic *pChr, NimBLEConnInfo &connInfo) override {
const std::string &v = pChr->getValue();
if (v.empty()) {
return; // empty Write -> ignore
}
digitalWrite(GPIO_MOTOR, v[0] ? HIGH : LOW);
}
};

class ServerCallbacks : public NimBLEServerCallbacks {
void onConnect(NimBLEServer *pServer, NimBLEConnInfo &connInfo) override {
Serial.println("Client connected");
}

void onDisconnect(NimBLEServer *pServer, NimBLEConnInfo &connInfo,
int reason) override {
Serial.printf("Client disconnected, reason=%d\n", reason);
digitalWrite(GPIO_MOTOR, LOW); // Failsafe: Motor off
NimBLEDevice::startAdvertising();
}
};

static MotorCallbacks motorCb;
static ServerCallbacks serverCb;

void setup() {
Serial.begin(115200);

pinMode(GPIO_MOTOR, OUTPUT);
digitalWrite(GPIO_MOTOR, LOW);

NimBLEDevice::init(RIGHT_MOTOR);

NimBLEServer *pServer = NimBLEDevice::createServer();
pServer->setCallbacks(&serverCb);

NimBLEService *pSvc = pServer->createService(SVC_UUID);

NimBLECharacteristic *pChr = pSvc->createCharacteristic(
CHR_UUID,
NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::WRITE_NR);
pChr->setCallbacks(&motorCb);

pSvc->start();

NimBLEAdvertising *pAdv = NimBLEDevice::getAdvertising();
pAdv->setName(RIGHT_MOTOR);
pAdv->addServiceUUID(SVC_UUID);
pAdv->enableScanResponse(true); // NimBLE 1.4.x: setScanResponse(true)
pAdv->start();

Serial.println("Advertising on");
}

void loop() {
// NimBLE is on in FreeRTOS-Task
delay(1000);
}