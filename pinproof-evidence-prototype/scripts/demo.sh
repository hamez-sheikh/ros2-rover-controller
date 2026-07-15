#!/usr/bin/env bash
# PinProof Week 1 demonstration: run all three fixture cases and verify that
# each produces the exit code the SCOPE.md decision table demands.
set -u
cd "$(dirname "$0")/.."

declare -i failures=0

run_case() {
    local name="$1" config="$2" expected_exit="$3" expectation="$4"
    echo
    echo "══════════════════════════════════════════════════════════════════"
    echo " CASE: ${name}   (expected: ${expectation}, exit ${expected_exit})"
    echo "══════════════════════════════════════════════════════════════════"
    pinproof scan --config "${config}"
    local actual=$?
    if [[ "${actual}" -eq "${expected_exit}" ]]; then
        echo "── exit code ${actual} == expected ${expected_exit}  ✔"
    else
        echo "── exit code ${actual} != expected ${expected_exit}  ✖  DEMO FAILURE"
        failures+=1
    fi
}

run_case "good"                   "fixtures/good/pinproof.yaml"                   0 "all PASS"
run_case "mismatch_sda"           "fixtures/mismatch_sda/pinproof.yaml"           1 "sensor_sda FAIL with evidence"
run_case "unsupported_expression" "fixtures/unsupported_expression/pinproof.yaml" 0 "sensor_sda UNKNOWN, not blocking"

echo
if [[ ${failures} -eq 0 ]]; then
    echo "All three cases behaved exactly as specified. Week 1 demonstration: ✔"
    exit 0
else
    echo "${failures} case(s) deviated from the specification. ✖"
    exit 1
fi
