import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import numpy as np
import time

class DemoPublisher(Node):
    def __init__(self):
        super().__init__('demo_publisher')
        self.pub_rgb = self.create_publisher(Image, '/camera/image_raw', 10)
        self.pub_depth = self.create_publisher(Image, '/camera/depth/image_raw', 10)
        self.timer = self.create_timer(1.0, self.timer_cb)

    def timer_cb(self):
        stamp = self.get_clock().now().to_msg()
        
        # Создаем RGB (красный квадрат в центре)
        rgb = np.zeros((6, 8, 3), dtype=np.uint8)
        rgb[2:4, 3:5] = [255, 0, 0]  # Красный
        msg_rgb = Image()
        msg_rgb.header.stamp = stamp
        msg_rgb.header.frame_id = 'camera_optical_frame'
        msg_rgb.height = 6
        msg_rgb.width = 8
        msg_rgb.encoding = 'rgb8'
        msg_rgb.step = 8 * 3
        msg_rgb.data = rgb.tobytes()

        # Создаем Depth (все пиксели = 1000 мм, т.е. 1 метр)
        depth = np.full((6, 8), 1000, dtype=np.uint16)
        msg_depth = Image()
        msg_depth.header.stamp = stamp
        msg_depth.header.frame_id = 'camera_optical_frame'
        msg_depth.height = 6
        msg_depth.width = 8
        msg_depth.encoding = '16UC1'
        msg_depth.step = 8 * 2
        msg_depth.data = depth.tobytes()

        # Отправляем сначала глубину, потом RGB
        self.pub_depth.publish(msg_depth)
        self.pub_rgb.publish(msg_rgb)
        self.get_logger().info('Sent test RGB/Depth pair')

def main(args=None):
    rclpy.init(args=args)
    node = DemoPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
