#include <Arduino.h>
#include <Wire.h>

#include "pins.h"

void setup() {
    Serial.begin(115200);
    pinMode(PIN_STATUS_LED, OUTPUT);
    Wire.begin(PIN_SENSOR_SDA, PIN_SENSOR_SCL);
}

void loop() {
    digitalWrite(PIN_STATUS_LED, HIGH);
    delay(500);
    digitalWrite(PIN_STATUS_LED, LOW);
    delay(500);
}
