import cv2
from cv_bridge import CvBridge
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image
from vision_msgs.msg import (
    Detection2D, Detection2DArray, Detection3D, Detection3DArray,
    ObjectHypothesis, ObjectHypothesisWithPose
)


class PerceptionNode(Node):
    def __init__(self):
        super().__init__('perception_node')
        self.bridge = CvBridge()
        self.depth_buffer = {}

        # Параметры из калибровки (примерные для 8x6)
        self.fx = 100.0
        self.fy = 100.0
        self.cx = 4.0
        self.cy = 3.0
        self.depth_scale_m = 0.001

        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.sub_rgb = self.create_subscription(
            Image, '/camera/image_raw', self.rgb_cb, sensor_qos)
        self.sub_depth = self.create_subscription(
            Image, '/camera/depth/image_raw', self.depth_cb, sensor_qos)

        self.pub_2d = self.create_publisher(
            Detection2DArray, '/perception/detections_2d', 10)
        self.pub_3d = self.create_publisher(
            Detection3DArray, '/perception/objects_3d', 10)
        self.pub_status = self.create_publisher(
            DiagnosticArray, '/perception/status', 10)

    def depth_cb(self, msg):
        # Буферизация глубины по штампу (время в секундах)
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        self.depth_buffer[round(stamp, 3)] = msg
        if len(self.depth_buffer) > 10:
            oldest = min(self.depth_buffer.keys())
            del self.depth_buffer[oldest]

    def rgb_cb(self, msg):
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        stamp_key = round(stamp, 3)

        # Конвертируем ROS Image в массив OpenCV (BGR)
        cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # Детектор красных связных областей
        lower_red1 = np.array([0, 0, 180])
        upper_red1 = np.array([120, 120, 255])
        mask = cv2.inRange(cv_img, lower_red1, upper_red1)

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections_2d = []
        bboxes = []

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            bboxes.append([x, y, w, h])

            det = Detection2D()
            det.header = msg.header
            hyp = ObjectHypothesisWithPose()
            hyp.hypothesis.class_id = 'cone'
            hyp.hypothesis.score = 1.0
            det.results.append(hyp)

            det.bbox.center.position.x = float(x + w / 2.0)
            det.bbox.center.position.y = float(y + h / 2.0)
            det.bbox.size_x = float(w)
            det.bbox.size_y = float(h)
            detections_2d.append(det)

        arr2d = Detection2DArray()
        arr2d.header = msg.header
        arr2d.detections = detections_2d
        self.pub_2d.publish(arr2d)

        # Обработка 3D
        arr3d = Detection3DArray()
        arr3d.header = msg.header

        status_msg = DiagnosticStatus()
        status_msg.name = 'perception'
        status_msg.level = DiagnosticStatus.OK
        status_msg.message = 'OK'

        depth_msg = self.depth_buffer.get(stamp_key)

        if depth_msg is None:
            if detections_2d:
                status_msg.level = DiagnosticStatus.WARN
                status_msg.message = 'missing_depth'
                status_msg.values.append(
                    KeyValue(key='reason', value='missing_depth'))
        elif depth_msg.header.frame_id != msg.header.frame_id:
            if detections_2d:
                status_msg.level = DiagnosticStatus.WARN
                status_msg.message = 'frame_mismatch'
                status_msg.values.append(
                    KeyValue(key='reason', value='frame_mismatch'))
        else:
            depth_img = self.bridge.imgmsg_to_cv2(
                depth_msg, desired_encoding='16UC1')
            for bbox in bboxes:
                x, y, w, h = bbox
                u = int(x + w // 2)
                v = int(y + h // 2)

                if v >= depth_img.shape[0] or u >= depth_img.shape[1]:
                    continue

                d_val = depth_img[v, u]
                if d_val == 0:
                    status_msg.level = DiagnosticStatus.WARN
                    status_msg.message = 'zero_depth'
                    status_msg.values.append(
                        KeyValue(key='reason', value='zero_depth'))
                    continue

                Z = d_val * self.depth_scale_m
                X = (u - self.cx) * Z / self.fx
                Y = (v - self.cy) * Z / self.fy

                det3d = Detection3D()
                det3d.header = msg.header
                hyp3d = ObjectHypothesis()
                hyp3d.class_id = 'cone'
                hyp3d.score = 1.0
                det3d.results.append(hyp3d)

                det3d.bbox.center.position.x = X
                det3d.bbox.center.position.y = Y
                det3d.bbox.center.position.z = Z
                det3d.bbox.size.x = 0.0
                det3d.bbox.size.y = 0.0
                det3d.bbox.size.z = 0.0
                arr3d.detections.append(det3d)

        self.pub_3d.publish(arr3d)

        diag_arr = DiagnosticArray()
        diag_arr.header = msg.header
        diag_arr.status.append(status_msg)
        self.pub_status.publish(diag_arr)


def main(args=None):
    rclpy.init(args=args)
    node = PerceptionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
