"""Unit tests for the rover's pure decision and motion logic.

These test rover_controller/rover_logic.py directly with plain pytest - no
ROS required - because that file has no ROS imports. The nodes call the same
functions, so these tests cover the real logic the robot runs.
"""

import math

from rover_controller.rover_logic import decide, normalize_angle, update_pose


# ---- decide(): the controller's brain ----

def test_clear_path_drives_forward():
    linear, angular, decision = decide(5.0, 0.1, 1.0, 0.75, 0.5, 0.8)
    assert decision == 'DRIVE FORWARD'
    assert linear == 0.5
    assert angular == 0.0


def test_range_at_threshold_turns():
    # Range exactly equal to safe_distance is not GREATER than it, so turn.
    linear, angular, decision = decide(1.0, 0.1, 1.0, 0.75, 0.5, 0.8)
    assert decision == 'TURN LEFT'
    assert linear == 0.0
    assert angular == 0.8


def test_range_below_threshold_turns():
    _, _, decision = decide(0.5, 0.1, 1.0, 0.75, 0.5, 0.8)
    assert decision == 'TURN LEFT'


def test_no_sensor_data_stops():
    linear, angular, decision = decide(None, None, 1.0, 0.75, 0.5, 0.8)
    assert decision == 'WAITING FOR SENSOR'
    assert linear == 0.0
    assert angular == 0.0


def test_stale_sensor_stops():
    linear, angular, decision = decide(5.0, 1.2, 1.0, 0.75, 0.5, 0.8)
    assert decision == 'SENSOR TIMEOUT - STOP'
    assert linear == 0.0
    assert angular == 0.0


# ---- normalize_angle() ----

def test_normalize_angle_wraps_large_angle():
    assert math.isclose(normalize_angle(3 * math.pi), math.pi, abs_tol=1e-9)


def test_normalize_angle_leaves_small_angle():
    assert math.isclose(normalize_angle(0.5), 0.5, abs_tol=1e-9)


# ---- update_pose(): the motion model ----

def test_update_pose_straight_line():
    x, y, heading = update_pose(0.0, 0.0, 0.0, 0.5, 0.0, 0.1)
    assert math.isclose(x, 0.05, abs_tol=1e-9)
    assert math.isclose(y, 0.0, abs_tol=1e-9)
    assert math.isclose(heading, 0.0, abs_tol=1e-9)


def test_update_pose_turning_changes_heading_only():
    x, y, heading = update_pose(0.0, 0.0, 0.0, 0.0, 0.8, 0.1)
    assert math.isclose(heading, 0.08, abs_tol=1e-9)
    assert math.isclose(x, 0.0, abs_tol=1e-9)
    assert math.isclose(y, 0.0, abs_tol=1e-9)
