#!/usr/bin/env python3
import json
import statistics

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener
from geometry_msgs.msg import PoseWithCovarianceStamped
from rosgraph_msgs.msg import Clock


class MeasureNode(Node):
    def __init__(self):
        super().__init__('measure_node')
        self.set_parameters([rclpy.parameter.Parameter('use_sim_time', rclpy.Parameter.Type.BOOL, True)])
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.sub_amcl = self.create_subscription(
            PoseWithCovarianceStamped, '/amcl_pose', self.amcl_cb, 10)
        self.sub_clock = self.create_subscription(
            Clock, '/clock', self.clock_cb, 10)

        self.t0 = None
        self.current_sim_time = None
        self.window_start = None
        self.window_end = None
        self.measuring = False

        self.tf_total = 0
        self.tf_success = 0
        self.covariances = []

        self.timer = self.create_timer(0.1, self.timer_cb)
        self.get_logger().info('Measure Node Started. Waiting for /clock...')

    def clock_cb(self, msg):
        t = msg.clock.sec + msg.clock.nanosec * 1e-9
        self.current_sim_time = t
        if self.t0 is None:
            self.t0 = t
            self.window_start = self.t0 + 10.0
            self.window_end = self.window_start + 20.0
            self.get_logger().info(
                f'Captured t0={self.t0}, window=[{self.window_start}, {self.window_end})')

    def amcl_cb(self, msg):
        if self.measuring and self.current_sim_time is not None:
            t_msg = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            if self.window_start <= t_msg < self.window_end:
                cov = msg.pose.covariance[0] + msg.pose.covariance[7]
                self.covariances.append(cov)

    def timer_cb(self):
        if self.current_sim_time is None:
            return
        now = self.current_sim_time

        if not self.measuring and now >= self.window_start:
            self.measuring = True
            self.get_logger().info('Starting measurement window...')

        if self.measuring and now < self.window_end:
            self.tf_total += 1
            try:
                self.tf_buffer.lookup_transform('map', 'odom', Time())
                self.tf_success += 1
            except Exception:
                pass

        if self.measuring and now >= self.window_end:
            self.measuring = False
            self.finish()
            rclpy.shutdown()

    def finish(self):
        ratio = self.tf_success / self.tf_total if self.tf_total > 0 else 0.0
        median_cov = statistics.median(self.covariances) if self.covariances else 0.0

        result = {
            "tf_queries_total": self.tf_total,
            "tf_queries_successful": self.tf_success,
            "tf_queries_ratio": ratio,
            "amcl_pose_count": len(self.covariances),
            "covariance_median": median_cov
        }
        self.get_logger().info(f"Measurement done: {json.dumps(result, indent=2)}")
        with open('/tmp/measure_result.json', 'w') as f:
            json.dump(result, f, indent=2)


def main(args=None):
    rclpy.init(args=args)
    node = MeasureNode()
    rclpy.spin(node)


if __name__ == '__main__':
    main()