# Development Log: ROS 2 Autonomous Rover Controller

This is an honest record of how I built this project, including the things that
went wrong and how I worked them out. I kept it because the problems taught me
more than the parts that worked on the first try. Most entries follow the same
shape: the problem, what caused it, how I figured it out, what I changed, and
what I took away.

## Getting a working environment

- **Problem:** I wanted to run ROS 2 on my Windows laptop and couldn't.
- **Cause:** WSL 2 kept failing to create its Linux virtual machine, with errors
  like `WslRegisterDistribution failed ... Catastrophic failure` and
  `Wsl/InstallDistro/.../E_UNEXPECTED`. Virtualization was enabled and the right
  Windows features were on, but it still wouldn't build the VM. Docker Desktop
  relied on the same WSL 2 backend, so it hit the same wall.
- **How I diagnosed it:** After many attempts I decided the problem was in my
  environment, not my project, and that I was burning time I could spend
  actually learning ROS.
- **What I changed:** I moved development into a browser-based GitHub Codespace,
  which runs Linux in the cloud, with no local install and no BIOS or Windows changes.
- **What I learned:** Sometimes the right move is to change the environment
  instead of fighting it.

## The graphical container that wouldn't show graphics

- **Problem:** My first Codespace image was a ROS desktop with a web (noVNC)
  view, but the desktop never loaded. The browser URL returned HTTP 401 and
  nothing was listening on port 80.
- **Cause:** The noVNC process kept crashing under its supervisor even though
  ROS itself was fine.
- **What I changed:** I switched to the official terminal-only image
  `ros:jazzy-ros-base`. My project doesn't need a GUI, so this deleted a whole
  category of problems.
- **What I learned:** Don't carry complexity you don't actually need.

## First ROS 2 package and a pub/sub sanity check

- I confirmed ROS worked with the built-in demo: `ros2 run demo_nodes_py talker`
  in one terminal and `ros2 run demo_nodes_py listener` in another. The listener
  received the talker's messages, which proved the environment was healthy.
- I created the package with
  `ros2 pkg create --build-type ament_python --license Apache-2.0 rover_controller`
  and the message dependencies (`rclpy`, `geometry_msgs`, `sensor_msgs`,
  `nav_msgs`), then built it with `colcon build --symlink-install`.
- **What I learned:** the workspace layout, where `src` holds my code, `build`/
  `install`/`log` are generated, and `source install/setup.bash` is what makes a
  terminal aware of my package.

## A syntax bug with a scary message

- **Problem:** A build failed with `SyntaxError: '(' was never closed` in
  `setup.py`.
- **Cause:** I had a missing closing parenthesis.
- **How I diagnosed it:** I read the actual error and line instead of guessing,
  and replaced the broken `setup.py` with a complete, valid version.
- **What I learned:** Read the real error message, since it usually points close to
  the problem.

## A file where I wanted a folder

- **Problem:** Trying to create my launch file gave
  `touch: cannot touch '.../launch/rover_system.launch.py': Not a directory`.
- **Cause:** I had accidentally created a *file* named `launch` instead of a
  *folder* named `launch`, so the path underneath it couldn't exist.
- **What I changed:** I renamed the stray file out of the way, made the real
  `launch/` folder, created the launch file inside it, and later deleted the
  leftover empty file after confirming it held nothing.
- **What I learned:** `mkdir` makes folders, `touch` makes files, and always
  check what something is before deleting it.

## From fake readings to a real feedback loop

- The first version of the range sensor just published fake, steadily
  decreasing numbers (5.00, 4.75, 4.50 ...). It looked convincing but wasn't
  connected to anything.
- I replaced it so the sensor subscribes to the rover's odometry, computes the
  real distance and bearing to a fixed obstacle at (4.0, 0.0), and only reports
  the obstacle when it's within the sensor's field of view.
- I then wrote the rover simulation (`rover_sim_node`), which takes velocity
  commands, updates its x/y/heading with simple 2D motion equations, and
  publishes odometry.
- Connecting the sensor to the rover's real position turned three separate
  programs into a genuine closed loop: position → sensor → decision → movement →
  new position.
- **What I learned:** a real feedback loop is very different from a script that
  just prints changing numbers.

## Launch file and parameters

- I added a launch file so one command starts every node instead of juggling
  several terminals.
- I moved the controller's settings (`safe_distance`, `forward_speed`,
  `turn_speed`) from hard-coded variables to ROS 2 parameters, and confirmed I
  could read and even change them live with `ros2 param set`.
- **What I learned:** parameters let you tune behaviour without editing and
  rebuilding code.

## The safety feature: timer-based control with a sensor timeout

- **Problem I was solving:** my original controller only acted when a sensor
  message arrived. If the sensor stopped, the controller would go silent and the
  rover would keep obeying its last command forever.
- **What I changed:** I rewrote the controller to run on a fixed 10 Hz timer.
  The sensor callback now only stores the latest reading and the time it
  arrived; the timer checks how old that reading is and, if nothing new has come
  in for 0.75 s, it publishes a zero-velocity stop (`SENSOR TIMEOUT - STOP`).
- **How I tested it:** I ran the three nodes in separate terminals, killed only
  the sensor, and watched the controller report the timeout within about 0.75 s
  and the rover freeze in place.
- **What I learned:** stale sensor data is dangerous, and separating "when I
  decide" from "when a message arrives" is what makes the stop reliable.

## A monitor node and quieter logs

- Watching four nodes print at once was noisy, so I added a read-only
  `monitor_node` that prints one clean status block per second.
- I then turned down the other logs: the sensor now only speaks up when the
  obstacle appears or disappears, so the monitor is the main thing you read.

## Cleaning up Ctrl+C

- **Problem:** stopping the system with Ctrl+C printed alarming red tracebacks.
- **Cause:** the nodes didn't handle the keyboard interrupt, and the controller
  tried to publish a final stop command after ROS had already begun shutting
  down.
- **What I changed:** I wrapped each node's spin in a try/except for the
  interrupt and used a safe shutdown, and made the controller's final stop
  best-effort so it can't crash on the way out. Now all four nodes report
  `finished cleanly`.
- **What I learned:** the difference between a real error and normal shutdown
  noise, and how to make shutdown tidy.

## Recording data with rosbag

- I recorded `/odom`, `/front_range`, and `/cmd_vel` with `ros2 bag record`,
  inspected the capture with `ros2 bag info`, and replayed it into just the
  monitor with `ros2 bag play`, and the dashboard came back to life from the
  recording alone.
- I added the bag folders to `.gitignore` so recordings never get committed.
- **What I learned:** why teams record and replay sensor data. You can debug
  and test against the exact same run over and over.

## Pulling out the logic so I could test it

- **Problem:** the decision-making and motion math were buried inside ROS nodes,
  which are hard to unit-test.
- **What I changed:** I moved that logic into a pure module, `rover_logic.py`,
  with no ROS imports, and had the nodes call it. Then I wrote nine `pytest`
  tests against it: clear path drives forward, exact threshold turns, obstacle
  turns, no data stops, stale data stops, angle wrapping, and the motion update
  for straight and turning motion.
- **What I learned:** separating pure logic from framework code makes it fast and
  simple to test, and the tests then cover the same code the robot actually runs.

## Cleanup and first real commit

- I wrote a `.gitignore` for `build/`, `install/`, `log/`, Python caches, and
  rosbag folders, fixed the package metadata (it still said `root` /
  `TODO`), and made my first honest commit capturing the whole working
  prototype. I deliberately did not fake a series of older commits.
- **What I learned:** what belongs in version control and what doesn't, and why
  an honest history matters.

## Adding a live browser view

- **Problem:** the terminal output is not much of a demo. I wanted to actually
  see the rover drive and dodge obstacles.
- **What I built:** a `sim_server_node` that generates an endless obstacle field
  and publishes the nearest-obstacle distance as the same `/front_range` message
  my controller already used, plus a tiny standard-library web server that a
  browser polls to draw the world with the camera following the rover.
- **Keeping it honest:** the browser makes no decisions. My real controller node
  still decides drive, turn, or stop over real ROS topics, and the page's buttons
  just set real ROS parameters. I also added a small stuck-recovery move to the
  controller so it never gets trapped in the endless field.
- **What I learned:** how to bridge ROS 2 to a browser with almost no extra
  tooling, and where to draw the line between the real robot logic and a display.
