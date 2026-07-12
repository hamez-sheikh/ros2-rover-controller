import json
import math
import os
import random
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import rclpy
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rcl_interfaces.msg import Parameter as ParameterMsg
from rcl_interfaces.msg import ParameterType, ParameterValue
from rcl_interfaces.srv import SetParameters
from rclpy.node import Node
from sensor_msgs.msg import Range

CELL = 4.0
START_CLEAR = 4.5


class World:
    """A deterministic, endless obstacle field, materialised only near the rover.

    Obstacles are generated per grid cell from a hash of the cell coordinates and
    a seed, so the same area always looks the same until the map is shuffled, and
    we never have to store the whole (infinite) world in memory.
    """

    def __init__(self):
        self.seed = 12345
        self.density = 0.35

    def _obstacle_in_cell(self, cx, cy):
        rng = random.Random((cx * 73856093) ^ (cy * 19349663) ^ (self.seed * 83492791))
        if rng.random() > self.density:
            return None
        radius = 0.5 + rng.random() * 0.4
        span = CELL / 2.0 - radius - 0.6
        if span < 0.0:
            span = 0.0
        x = cx * CELL + (rng.random() * 2.0 - 1.0) * span
        y = cy * CELL + (rng.random() * 2.0 - 1.0) * span
        if math.hypot(x, y) < START_CLEAR:
            return None
        return (x, y, radius)

    def nearby(self, rx, ry, reach):
        cells = int(reach / CELL) + 1
        cx0 = int(round(rx / CELL))
        cy0 = int(round(ry / CELL))
        found = []
        for cx in range(cx0 - cells, cx0 + cells + 1):
            for cy in range(cy0 - cells, cy0 + cells + 1):
                obstacle = self._obstacle_in_cell(cx, cy)
                if obstacle is None:
                    continue
                if math.hypot(obstacle[0] - rx, obstacle[1] - ry) <= reach + obstacle[2]:
                    found.append(obstacle)
        return found


def nearest_in_fov(obstacles, rx, ry, heading, half_fov, max_range):
    """Distance to the nearest obstacle surface inside the sensor's cone."""
    best = max_range
    for (ox, oy, orr) in obstacles:
        dx = ox - rx
        dy = oy - ry
        centre = math.hypot(dx, dy)
        surface = centre - orr
        if surface < 0.0:
            surface = 0.0
        bearing = math.atan2(dy, dx) - heading
        bearing = math.atan2(math.sin(bearing), math.cos(bearing))
        angular_size = math.asin(min(1.0, orr / max(centre, 1e-3)))
        if abs(bearing) - angular_size <= half_fov and surface <= max_range:
            if surface < best:
                best = surface
    return best


class SimServerNode(Node):
    """Simulated endless world + multi-obstacle sensor + a tiny web server.

    ROS role: publishes /front_range (the same message the real controller
    already consumes) from a procedurally generated obstacle field.
    Web role: serves a browser visualisation and receives simple controls.
    It makes no driving decisions; the controller does.
    """

    def __init__(self):
        super().__init__('sim_server_node')
        self.declare_parameter('port', 8080)
        self.declare_parameter('field_of_view', 0.9)
        self.declare_parameter('sensor_range', 3.0)
        self.declare_parameter('max_range', 6.0)
        self.declare_parameter('min_range', 0.1)
        self.declare_parameter('publish_rate', 15.0)
        self.declare_parameter('obstacle_density', 0.35)

        self.field_of_view = self.get_parameter('field_of_view').value
        self.sensor_range = self.get_parameter('sensor_range').value
        self.max_range = self.get_parameter('max_range').value
        self.min_range = self.get_parameter('min_range').value

        self.world = World()
        self.world.density = self.get_parameter('obstacle_density').value

        self.lock = threading.Lock()
        self.rover = {'x': 0.0, 'y': 0.0, 'heading': 0.0}
        self.cmd = {'linear': 0.0, 'angular': 0.0}
        self.snapshot = {
            'rover': dict(self.rover),
            'obstacles': [],
            'behaviour': 'waiting',
            'sensor': self.max_range,
            'fov': self.field_of_view,
            'range': self.sensor_range,
            'paused': False,
            'speed': 0.5,
            'density': self.world.density,
        }

        self.paused = False
        self.base_speed = 0.5
        self.base_turn = 0.8
        self.params_dirty = True

        self.range_pub = self.create_publisher(Range, '/front_range', 10)
        self.create_subscription(Odometry, '/odom', self.on_odom, 10)
        self.create_subscription(Twist, '/cmd_vel', self.on_cmd, 10)
        self.param_client = self.create_client(SetParameters, '/controller_node/set_parameters')

        rate = self.get_parameter('publish_rate').value
        self.timer = self.create_timer(1.0 / rate, self.tick)

        self.port = int(self.get_parameter('port').value)
        self.httpd = None
        self._start_server()
        self.get_logger().info(
            'Sim server ready. Forward and open port '
            f'{self.port} in your browser.'
        )

    def on_odom(self, msg):
        q = msg.pose.pose.orientation
        sin_yaw = 2.0 * (q.w * q.z + q.x * q.y)
        cos_yaw = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        with self.lock:
            self.rover['x'] = msg.pose.pose.position.x
            self.rover['y'] = msg.pose.pose.position.y
            self.rover['heading'] = math.atan2(sin_yaw, cos_yaw)

    def on_cmd(self, msg):
        with self.lock:
            self.cmd['linear'] = msg.linear.x
            self.cmd['angular'] = msg.angular.z

    def tick(self):
        with self.lock:
            rx = self.rover['x']
            ry = self.rover['y']
            rh = self.rover['heading']
            lin = self.cmd['linear']
            ang = self.cmd['angular']
            paused = self.paused
            base_speed = self.base_speed
            base_turn = self.base_turn
            dirty = self.params_dirty
            self.params_dirty = False

        obstacles = self.world.nearby(rx, ry, self.sensor_range + 1.0)
        distance = nearest_in_fov(
            obstacles, rx, ry, rh, self.field_of_view / 2.0, self.max_range
        )
        distance = max(distance, self.min_range)

        message = Range()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = 'front_sensor'
        message.radiation_type = Range.INFRARED
        message.field_of_view = self.field_of_view
        message.min_range = self.min_range
        message.max_range = self.max_range
        message.range = float(distance)
        self.range_pub.publish(message)

        if paused:
            behaviour = 'paused'
        elif lin < -0.01:
            behaviour = 'recovering'
        elif lin > 0.01:
            behaviour = 'driving'
        elif abs(ang) > 0.01:
            behaviour = 'avoiding'
        else:
            behaviour = 'stopped'

        view = self.world.nearby(rx, ry, 13.0)
        with self.lock:
            self.snapshot = {
                'rover': {'x': rx, 'y': ry, 'heading': rh},
                'obstacles': [[round(o[0], 3), round(o[1], 3), round(o[2], 3)] for o in view],
                'behaviour': behaviour,
                'sensor': round(min(distance, self.max_range), 3),
                'fov': self.field_of_view,
                'range': self.sensor_range,
                'paused': paused,
                'speed': round(base_speed, 2),
                'density': round(self.world.density, 2),
            }

        if dirty:
            self._apply_controller_params(paused, base_speed, base_turn)

    def _apply_controller_params(self, paused, base_speed, base_turn):
        if not self.param_client.service_is_ready():
            with self.lock:
                self.params_dirty = True
            return
        forward = 0.0 if paused else base_speed
        turn = 0.0 if paused else base_turn
        request = SetParameters.Request()
        for name, value in (('forward_speed', forward), ('turn_speed', turn)):
            param = ParameterMsg()
            param.name = name
            param.value = ParameterValue(
                type=ParameterType.PARAMETER_DOUBLE, double_value=float(value)
            )
            request.parameters.append(param)
        self.param_client.call_async(request)

    def handle_control(self, query):
        with self.lock:
            action = query.get('action', [None])[0]
            if action == 'pause':
                self.paused = True
                self.params_dirty = True
            elif action == 'resume':
                self.paused = False
                self.params_dirty = True
            elif action in ('shuffle', 'restart'):
                self.world.seed = random.randint(1, 1000000000)
            if 'speed' in query:
                try:
                    self.base_speed = max(0.0, min(1.5, float(query['speed'][0])))
                    self.params_dirty = True
                except ValueError:
                    pass
            if 'density' in query:
                try:
                    self.world.density = max(0.05, min(0.7, float(query['density'][0])))
                except ValueError:
                    pass

    def _start_server(self):
        node = self
        share = get_package_share_directory('rover_controller')
        html_path = os.path.join(share, 'web', 'index.html')

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _send(self, code, body, content_type):
                self.send_response(code)
                self.send_header('Content-Type', content_type)
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                parsed = urlparse(self.path)
                if parsed.path in ('/', '/index.html'):
                    try:
                        with open(html_path, 'rb') as handle:
                            body = handle.read()
                    except OSError:
                        body = b'<h1>index.html was not installed</h1>'
                    self._send(200, body, 'text/html; charset=utf-8')
                elif parsed.path == '/state':
                    with node.lock:
                        body = json.dumps(node.snapshot).encode('utf-8')
                    self._send(200, body, 'application/json')
                elif parsed.path == '/control':
                    node.handle_control(parse_qs(parsed.query))
                    self._send(200, b'{"ok":true}', 'application/json')
                else:
                    self._send(404, b'not found', 'text/plain')

        self.httpd = ThreadingHTTPServer(('0.0.0.0', self.port), Handler)
        thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        thread.start()


def main(args=None):
    rclpy.init(args=args)
    node = SimServerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.httpd is not None:
            node.httpd.shutdown()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
