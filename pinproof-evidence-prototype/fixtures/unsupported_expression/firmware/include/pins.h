// Pin map for the PinProof "unsupported_expression" fixture.
// PIN_SENSOR_SDA is chosen at RUNTIME from an array — a real pattern in
// multi-variant firmware, and exactly what a line-level extractor must NOT
// pretend to understand. Expected verdict: UNKNOWN (unsupported-expression),
// never PASS and never a CI-blocking FAIL.
#pragma once

#include <Arduino.h>

extern const int SDA_PIN_OPTIONS[2];
int selectBoardRevision();

const int PIN_SENSOR_SDA = SDA_PIN_OPTIONS[selectBoardRevision()];
#define PIN_SENSOR_SCL 17

constexpr int PIN_STATUS_LED = GPIO_NUM_4;
