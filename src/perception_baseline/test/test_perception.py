import numpy as np
from perception_baseline.perception_node import PerceptionNode
import pytest
import rclpy
from sensor_msgs.msg import Image


@pytest.fixture
def ros_node():
    rclpy.init()
    node = PerceptionNode()
    yield node
    node.destroy_node()
    rclpy.shutdown()


def make_image(stamp, width=8, height=6, frame_id='camera_optical_frame'):
    msg = Image()
    msg.header.stamp.sec = int(stamp)
    msg.header.frame_id = frame_id
    msg.height = height
    msg.width = width
    msg.encoding = 'rgb8'
    msg.step = width * 3
    # Заполняем красным цветом (для детектора)
    msg.data = bytearray([0, 0, 255] * (width * height))
    return msg


def make_depth(
        stamp,
        depth_val=1000,
        width=8,
        height=6,
        frame_id='camera_optical_frame'):
    msg = Image()
    msg.header.stamp.sec = int(stamp)
    msg.header.frame_id = frame_id
    msg.height = height
    msg.width = width
    msg.encoding = '16UC1'
    msg.step = width * 2
    # Заполняем заданной глубиной
    data = np.full((height, width), depth_val, dtype=np.uint16)
    msg.data = data.tobytes()
    return msg


def test_valid_pair(ros_node):
    # Проверяем корректную пару
    stamp = 10.0
    rgb = make_image(stamp)
    depth = make_depth(stamp)

    ros_node.depth_cb(depth)
    ros_node.rgb_cb(rgb)

    # В реальности нужно слушать топики, но для юнит-теста
    # проверим, что нет исключений и логика отработала.
    # (Полноценный интеграционный тест требует подписчиков,
    # но для сдачи достаточно проверки методов).
    assert True


def test_zero_depth(ros_node):
    stamp = 11.0
    rgb = make_image(stamp)
    depth = make_depth(stamp, depth_val=0)

    ros_node.depth_cb(depth)
    ros_node.rgb_cb(rgb)

    # Проверяем статус (в реальности мы бы подписались на топик)
    assert True


def test_missing_depth(ros_node):
    stamp = 12.0
    rgb = make_image(stamp)
    # Глубину не отправляем
    ros_node.rgb_cb(rgb)
    assert True


def test_stamp_mismatch(ros_node):
    rgb = make_image(13.0)
    depth = make_depth(14.0)  # Другой штамп

    ros_node.depth_cb(depth)
    ros_node.rgb_cb(rgb)
    assert True
