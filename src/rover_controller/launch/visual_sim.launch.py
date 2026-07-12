from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rover_controller',
            executable='rover_sim',
            output='screen',
        ),
        Node(
            package='rover_controller',
            executable='controller',
            output='screen',
            parameters=[
                {
                    'safe_distance': 1.0,
                    'forward_speed': 0.5,
                    'turn_speed': 0.8,
                    'control_rate': 10.0,
                    'sensor_timeout': 0.75,
                    'recovery_time': 4.0,
                    'recovery_duration': 1.2,
                }
            ],
        ),
        Node(
            package='rover_controller',
            executable='sim_server',
            output='screen',
            parameters=[
                {
                    'port': 8080,
                    'obstacle_density': 0.35,
                }
            ],
        ),
    ])
