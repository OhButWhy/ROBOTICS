from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose


class Patrol(Node):
    def __init__(self):
        super().__init__('patrol')

        self._pose = None
        self._sub = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self._on_pose,
            10,
        )
        self._pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self._timer = self.create_timer(0.1, self._on_timer)

    def _on_pose(self, msg):
        self._pose = msg

    def _on_timer(self):
        cmd = command_from_pose(self._pose)
        self._pub.publish(cmd)


def command_from_pose(pose):
    cmd = Twist()
    if pose is None:
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
    else:
        cmd.linear.x = 0.5
        cmd.angular.z = 0.3
    return cmd


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
