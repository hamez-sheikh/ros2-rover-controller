import math

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Range


class MonitorNode(Node):
    """Listens to every topic and prints one clean status summary each second."""

    def __init__(self):
        super().__init__('monitor_node')

        # Latest values seen on each topic. None means "nothing received yet".
        self.x_position = None
        self.y_position = None
        self.heading = None
        self.front_range = None
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0

        # Subscribe to the three topics the other nodes publish.
        self.create_subscription(Odometry, '/odom', self.odometry_callback, 10)
        self.create_subscription(Range, '/front_range', self.range_callback, 10)
        self.create_subscription(Twist, '/cmd_vel', self.command_callback, 10)

        # Print one summary per second (1 Hz).
        self.summary_timer = self.create_timer(1.0, self.print_summary)

        self.get_logger().info(
            'Monitor node started. Printing a status summary every second.'
        )

    def odometry_callback(self, odometry_message):
        """Store the rover's latest position and heading."""
        self.x_position = odometry_message.pose.pose.position.x
        self.y_position = odometry_message.pose.pose.position.y
        orientation = odometry_message.pose.pose.orientation
        sin_yaw = 2.0 * (
            orientation.w * orientation.z + orientation.x * orientation.y
        )
        cos_yaw = 1.0 - 2.0 * (
            orientation.y * orientation.y + orientation.z * orientation.z
        )
        self.heading = math.atan2(sin_yaw, cos_yaw)

    def range_callback(self, range_message):
        """Store the latest front-range measurement."""
        self.front_range = range_message.range

    def command_callback(self, command_message):
        """Store the latest movement command."""
        self.linear_velocity = command_message.linear.x
        self.angular_velocity = command_message.angular.z

    def describe_state(self):
        """Turn the latest command into a simple, readable state name."""
        if self.linear_velocity > 0.0:
            return 'DRIVING'
        if self.angular_velocity != 0.0:
            return 'TURNING'
        return 'STOPPED'

    def print_summary(self):
        """Print one tidy block describing the whole system."""
        if self.x_position is None:
            self.get_logger().info('Waiting for data from the rover...')
            return

        range_text = (
            f'{self.front_range:.2f} m'
            if self.front_range is not None
            else 'no reading'
        )

        self.get_logger().info(
            '\n'
            f'  Position: ({self.x_position:.2f}, {self.y_position:.2f}) m\n'
            f'  Heading:  {self.heading:.2f} rad\n'
            f'  Range:    {range_text}\n'
            f'  Linear:   {self.linear_velocity:.2f} m/s\n'
            f'  Angular:  {self.angular_velocity:.2f} rad/s\n'
            f'  State:    {self.describe_state()}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = MonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
