import math

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node

from rover_controller.rover_logic import update_pose


class RoverSimNode(Node):
    """Simulates rover movement using velocity commands from /cmd_vel."""

    def __init__(self):
        super().__init__('rover_sim_node')
        # The simulated rover begins at the origin.
        self.x_position = 0.0
        self.y_position = 0.0
        self.heading = 0.0
        # The rover begins stopped.
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        # The simulation updates every 0.1 seconds, or 10 times per second.
        self.time_step = 0.1
        self.command_subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.command_callback,
            10
        )
        self.odometry_publisher = self.create_publisher(
            Odometry,
            '/odom',
            10
        )
        self.simulation_timer = self.create_timer(
            self.time_step,
            self.update_rover
        )
        self.log_counter = 0
        self.get_logger().info('Rover simulation node has started.')

    def command_callback(self, command_message):
        """Store the newest movement command from the controller."""
        self.linear_velocity = command_message.linear.x
        self.angular_velocity = command_message.angular.z

    def update_rover(self):
        """Update the rover position and publish its odometry."""
        # The motion math lives in the pure, unit-tested update_pose function.
        self.x_position, self.y_position, self.heading = update_pose(
            self.x_position,
            self.y_position,
            self.heading,
            self.linear_velocity,
            self.angular_velocity,
            self.time_step,
        )
        odometry_message = Odometry()
        odometry_message.header.stamp = (
            self.get_clock().now().to_msg()
        )
        odometry_message.header.frame_id = 'odom'
        odometry_message.child_frame_id = 'base_link'
        odometry_message.pose.pose.position.x = self.x_position
        odometry_message.pose.pose.position.y = self.y_position
        odometry_message.pose.pose.position.z = 0.0
        odometry_message.pose.pose.orientation.x = 0.0
        odometry_message.pose.pose.orientation.y = 0.0
        odometry_message.pose.pose.orientation.z = math.sin(
            self.heading / 2.0
        )
        odometry_message.pose.pose.orientation.w = math.cos(
            self.heading / 2.0
        )
        odometry_message.twist.twist.linear.x = self.linear_velocity
        odometry_message.twist.twist.angular.z = self.angular_velocity
        self.odometry_publisher.publish(odometry_message)
        self.log_counter += 1
        if self.log_counter >= 10:
            self.get_logger().info(
                f'Position: ({self.x_position:.2f}, '
                f'{self.y_position:.2f}) m | '
                f'Heading: {self.heading:.2f} rad | '
                f'Linear: {self.linear_velocity:.2f} m/s | '
                f'Angular: {self.angular_velocity:.2f} rad/s'
            )
            self.log_counter = 0


def main(args=None):
    rclpy.init(args=args)
    node = RoverSimNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
