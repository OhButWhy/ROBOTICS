import math

from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


class OdomAdapter(Node):
    def __init__(self):
        super().__init__('odom_adapter')
        self.pub = self.create_publisher(Odometry, '/vehicle/odom', 10)
        self.sub = self.create_subscription(
            Odometry, '/vehicle/odom_gz', self.callback, 10)
        self.tf_broadcaster = TransformBroadcaster(self)

    def callback(self, msg):
        # Проверка исходных фреймов
        if msg.header.frame_id != 'course_ackermann/odom' or \
           msg.child_frame_id != 'course_ackermann/base_link':
            return

        # Проверка на NaN
        if math.isnan(msg.pose.pose.position.x) or math.isnan(msg.pose.pose.position.y):
            return

        # Нормализация
        msg.header.frame_id = 'odom'
        msg.child_frame_id = 'base_link'

        self.pub.publish(msg)

        t = TransformStamped()
        t.header.stamp = msg.header.stamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z
        t.transform.rotation = msg.pose.pose.orientation
        self.tf_broadcaster.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = OdomAdapter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
