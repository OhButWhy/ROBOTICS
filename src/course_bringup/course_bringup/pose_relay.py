import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from turtlesim.msg import Pose


class PoseRelay(Node):
    def __init__(self):
        super().__init__('pose_relay')

        best_effort_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self._pub = self.create_publisher(Pose, 'sensor_pose', best_effort_qos)
        self._sub = self.create_subscription(
            Pose, 'turtle1/pose', self._on_pose, 10,
        )

    def _on_pose(self, msg):
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = PoseRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
