import math

from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from rclpy.time import Time


def calculate_twist(speed, angle, L=0.8):
    """Чистая функция для перевода Ackermann в Twist."""
    if math.isnan(speed) or math.isinf(speed) or math.isnan(angle) or math.isinf(angle):
        return Twist()  # нулевая команда

    v = max(0.0, min(speed, 1.2))
    delta = max(-0.45, min(angle, 0.45))

    twist = Twist()
    twist.linear.x = v
    if v > 1e-4:
        twist.angular.z = v * math.tan(delta) / L
    else:
        twist.angular.z = 0.0

    return twist


class AckermannAdapter(Node):
    def __init__(self):
        super().__init__('ackermann_adapter')
        self.pub = self.create_publisher(Twist, '/vehicle/gz_cmd_vel', 10)
        self.sub = self.create_subscription(
            AckermannDriveStamped, '/drive/safe', self.callback, 10)
        self.L = 0.8

    def callback(self, msg):
        now = self.get_clock().now()
        msg_time = Time.from_msg(msg.header.stamp)
        age = (now - msg_time).nanoseconds / 1e9

        if age > 0.25:
            self.get_logger().warn('Stale command. Zeroing.')
            self.pub.publish(Twist())
            return

        twist = calculate_twist(
            msg.drive.speed, msg.drive.steering_angle, self.L)
        self.pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = AckermannAdapter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
