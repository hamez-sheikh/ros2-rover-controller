// Pin map for the PinProof "good" fixture.
// PIN_SENSOR_SDA goes through one alias step on purpose, to exercise the
// deterministic alias resolution (SCOPE.md §3).
#pragma once

#include <Arduino.h>

#define SDA_GPIO 18
#define PIN_SENSOR_SDA SDA_GPIO
#define PIN_SENSOR_SCL 17

constexpr int PIN_STATUS_LED = GPIO_NUM_4;
