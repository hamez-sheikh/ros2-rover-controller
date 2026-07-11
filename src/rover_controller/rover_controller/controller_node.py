import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import Range

from rover_controller.rover_logic import decide


class ControllerNode(Node):
    """Runs a timer-based rover controller with sensor-timeout protection."""

    def __init__(self):
        super().__init__('controller_node')
        # Configurable controller parameters.
        self.declare_parameter('safe_distance', 1.0)
        self.declare_parameter('forward_speed', 0.5)
        self.declare_parameter('turn_speed', 0.8)
        self.declare_parameter('control_rate', 10.0)
        self.declare_parameter('sensor_timeout', 0.75)
        # Latest sensor information.
        self.latest_range = None
        self.last_sensor_time = None
        self.command_publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )
        self.range_subscription = self.create_subscription(
            Range,
            '/front_range',
            self.range_callback,
            10
        )
        control_rate = self.get_parameter('control_rate').value
        timer_period = 1.0 / control_rate
        self.control_timer = self.create_timer(
            timer_period,
            self.control_loop
        )
        self.previous_decision = None
        self.get_logger().info(
            'Controller started. '
            f'Control rate: {control_rate:.1f} Hz'
        )

    def range_callback(self, range_message):
        """Store the newest sensor measurement and its arrival time."""
        self.latest_range = range_message.range
        self.last_sensor_time = self.get_clock().now()

    def control_loop(self):
        """Publish a safe movement command at a fixed rate."""
        safe_distance = self.get_parameter('safe_distance').value
        forward_speed = self.get_parameter('forward_speed').value
        turn_speed = self.get_parameter('turn_speed').value
        sensor_timeout = self.get_parameter('sensor_timeout').value

        # How many seconds since the last reading? None means none yet.
        if self.last_sensor_time is None:
            sensor_age = None
        else:
            sensor_age = (
                self.get_clock().now() - self.last_sensor_time
            ).nanoseconds / 1_000_000_000

        # The decision is made by the pure, unit-tested logic function.
        linear, angular, decision = decide(
            self.latest_range,
            sensor_age,
            safe_distance,
            sensor_timeout,
            forward_speed,
            turn_speed,
        )

        command = Twist()
        command.linear.x = linear
        command.angular.z = angular
        self.command_publisher.publish(command)

        # Only print when the decision changes, avoiding excessive output.
        if decision != self.previous_decision:
            range_text = (
                f'{self.latest_range:.2f} m'
                if self.latest_range is not None
                else 'none'
            )
            self.get_logger().info(
                f'Range: {range_text} | '
                f'Decision: {decision} | '
                f'Linear: {command.linear.x:.2f} m/s | '
                f'Angular: {command.angular.z:.2f} rad/s'
            )
            self.previous_decision = decision


def main(args=None):
    rclpy.init(args=args)
    node = ControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.command_publisher.publish(Twist())
        except Exception:
            pass
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
