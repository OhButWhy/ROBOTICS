import math

from geometry_msgs.msg import Twist
from rcl_interfaces.msg import SetParametersResult
import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose


class Patrol(Node):
    def __init__(self):
        super().__init__('patrol')

        self.declare_parameter('linear_speed', 0.5)
        self.declare_parameter('turn_rate', 0.3)
        self.declare_parameter('publish_hz', 10.0)
        self.add_on_set_parameters_callback(self._on_param_change)

        self._pose = None
        self._sub = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self._on_pose,
            10,
        )
        self._pub = self.create_publisher(Twist, 'cmd_vel', 10)

        hz = self.get_parameter('publish_hz').value
        self._timer = self.create_timer(1.0 / hz, self._on_timer)

    def _on_pose(self, msg):
        self._pose = msg

    def _on_timer(self):
        cmd = command_from_pose(self._pose,
                                self.get_parameter('linear_speed').value,
                                self.get_parameter('turn_rate').value,)
        self._pub.publish(cmd)

    def _restart_timer(self, hz):
        if self._timer is not None:
            self._timer.cancel()
            self.destroy_timer(self._timer)
        self._timer = self.create_timer(1.0 / hz, self._on_timer)

    def _on_param_change(self, params):
        for p in params:
            if not validate_param(p.name, p.value):
                return SetParametersResult(
                    successful=False,
                    reason=f'{p.name}={p.value} недопустимо',
                )
        for p in params:
            if p.name == 'publish_hz':
                self._restart_timer(p.value)

        return SetParametersResult(successful=True)


def command_from_pose(pose, linear_speed, turn_rate):
    cmd = Twist()
    if pose is None:
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
    else:
        cmd.linear.x = linear_speed
        cmd.angular.z = turn_rate
    return cmd


def validate_param(name, value):
    if value is None or not isinstance(value, (int, float)):
        return False
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return False
    if name == 'linear_speed':
        return 0.0 <= value <= 1.0
    if name == 'turn_rate':
        return -1.0 <= value <= 1.0
    if name == 'publish_hz':
        return 1.0 <= value <= 30.0
    return False


def main(args=None):
    rclpy.init(args=args)
    node = Patrol()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
