"""Pure decision and motion helpers for the rover, with no ROS imports.

Keeping this logic separate from the ROS nodes lets us unit-test the rover's
'brain' (decide) and its physics (update_pose) with plain pytest, no ROS
required. The nodes import these functions so the tests cover real code.
"""

import math


def normalize_angle(angle):
    """Wrap an angle into the range -pi .. +pi radians."""
    return math.atan2(math.sin(angle), math.cos(angle))


def decide(latest_range, sensor_age, safe_distance, sensor_timeout,
           forward_speed, turn_speed):
    """Choose a movement command from the latest sensor reading.

    Returns a tuple: (linear_velocity, angular_velocity, decision_text).

    sensor_age is the number of seconds since the last reading arrived, or
    None if no reading has ever arrived yet.
    """
    if sensor_age is None:
        return 0.0, 0.0, 'WAITING FOR SENSOR'
    if sensor_age > sensor_timeout:
        return 0.0, 0.0, 'SENSOR TIMEOUT - STOP'
    if latest_range > safe_distance:
        return forward_speed, 0.0, 'DRIVE FORWARD'
    return 0.0, turn_speed, 'TURN LEFT'


def update_pose(x, y, heading, linear_velocity, angular_velocity, time_step):
    """Advance the rover one time step; return the new (x, y, heading)."""
    x += linear_velocity * math.cos(heading) * time_step
    y += linear_velocity * math.sin(heading) * time_step
    heading += angular_velocity * time_step
    heading = normalize_angle(heading)
    return x, y, heading
