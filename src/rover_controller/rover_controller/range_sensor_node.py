import math

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Range

from rover_controller.rover_logic import normalize_angle


class RangeSensorNode(Node):
    """Simulates a front-facing sensor detecting one fixed obstacle."""

    def __init__(self):
        super().__init__('range_sensor_node')
        # The simulated obstacle's position in the map.
        self.obstacle_x = 4.0
        self.obstacle_y = 0.0
        # Latest rover state received from /odom.
        self.rover_x = 0.0
        self.rover_y = 0.0
        self.rover_heading = 0.0
        self.received_odometry = False
        # Simulated sensor specifications.
        self.minimum_range = 0.1
        self.maximum_range = 6.0
        self.field_of_view = 0.8
        # Remember the last visibility so we only log when it changes.
        self.previous_visibility = None
        self.range_publisher = self.create_publisher(
            Range,
            '/front_range',
            10
        )
        self.odometry_subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odometry_callback,
            10
        )
        # Publish a sensor reading five times per second.
        self.sensor_timer = self.create_timer(
            0.2,
            self.publish_range
        )
        self.get_logger().info(
            'Range sensor started. '
            'Obstacle is located at (4.0, 0.0) m.'
        )

    def odometry_callback(self, odometry_message):
        """Store the newest rover position and heading."""
        self.rover_x = odometry_message.pose.pose.position.x
        self.rover_y = odometry_message.pose.pose.position.y
        orientation = odometry_message.pose.pose.orientation
        sin_yaw = 2.0 * (
            orientation.w * orientation.z
            + orientation.x * orientation.y
        )
        cos_yaw = 1.0 - 2.0 * (
            orientation.y * orientation.y
            + orientation.z * orientation.z
        )
        self.rover_heading = math.atan2(sin_yaw, cos_yaw)
        self.received_odometry = True

    def publish_range(self):
        """Calculate and publish the obstacle measurement."""
        if not self.received_odometry:
            return
        x_difference = self.obstacle_x - self.rover_x
        y_difference = self.obstacle_y - self.rover_y
        obstacle_distance = math.hypot(
            x_difference,
            y_difference
        )
        obstacle_direction = math.atan2(
            y_difference,
            x_difference
        )
        angle_difference = normalize_angle(
            obstacle_direction - self.rover_heading
        )
        obstacle_is_visible = (
            abs(angle_difference) <= self.field_of_view / 2.0
            and obstacle_distance <= self.maximum_range
        )
        if obstacle_is_visible:
            measured_range = max(
                obstacle_distance,
                self.minimum_range
            )
            visibility = 'VISIBLE'
        else:
            measured_range = self.maximum_range
            visibility = 'NOT VISIBLE'
        range_message = Range()
        range_message.header.stamp = (
            self.get_clock().now().to_msg()
        )
        range_message.header.frame_id = 'front_sensor'
        range_message.radiation_type = Range.INFRARED
        range_message.field_of_view = self.field_of_view
        range_message.min_range = self.minimum_range
        range_message.max_range = self.maximum_range
        range_message.range = measured_range
        self.range_publisher.publish(range_message)
        # Only log when the obstacle appears or disappears, to avoid spam.
        if visibility != self.previous_visibility:
            self.get_logger().info(
                f'Obstacle now {visibility} | '
                f'Rover: ({self.rover_x:.2f}, {self.rover_y:.2f}) m | '
                f'Range: {measured_range:.2f} m'
            )
            self.previous_visibility = visibility


def main(args=None):
    rclpy.init(args=args)
    node = RangeSensorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
