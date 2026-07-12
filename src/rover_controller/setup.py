import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'rover_controller'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name],
        ),
        (
            'share/' + package_name,
            ['package.xml'],
        ),
        (
            os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py'),
        ),
        (
            os.path.join('share', package_name, 'web'),
            glob('web/*'),
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Hamez Sheikh',
    maintainer_email='hamezys@gmail.com',
    description=(
        'Software-only simulated rover with a closed-loop '
        'obstacle-avoidance controller in ROS 2 Jazzy.'
    ),
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'range_sensor = rover_controller.range_sensor_node:main',
            'controller = rover_controller.controller_node:main',
            'rover_sim = rover_controller.rover_sim_node:main',
            'monitor = rover_controller.monitor_node:main',
            'sim_server = rover_controller.sim_server_node:main',
        ],
    },
)
