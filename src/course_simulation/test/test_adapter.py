import math

from course_simulation.ackermann_adapter import calculate_twist
import pytest

L = 0.8  # База


def test_straight_drive():
    twist = calculate_twist(1.0, 0.0, L)
    assert pytest.approx(twist.linear.x) == 1.0
    assert pytest.approx(twist.angular.z) == 0.0


def test_turning():
    twist = calculate_twist(1.0, 0.45, L)
    expected_omega = 1.0 * math.tan(0.45) / L
    assert pytest.approx(twist.linear.x) == 1.0
    assert pytest.approx(twist.angular.z) == expected_omega


def test_zero_speed():
    twist = calculate_twist(0.0, 0.45, L)
    assert pytest.approx(twist.linear.x) == 0.0
    assert pytest.approx(twist.angular.z) == 0.0


def test_nan_values():
    twist_nan_speed = calculate_twist(float('nan'), 0.0, L)
    assert twist_nan_speed.linear.x == 0.0
    assert twist_nan_speed.angular.z == 0.0

    twist_nan_angle = calculate_twist(1.0, float('nan'), L)
    assert twist_nan_angle.linear.x == 0.0
    assert twist_nan_angle.angular.z == 0.0


def test_clamping():
    twist_over = calculate_twist(5.0, 1.0, L)
    assert twist_over.linear.x == 1.2
    expected_omega = 1.2 * math.tan(0.45) / L
    assert pytest.approx(twist_over.angular.z) == expected_omega
