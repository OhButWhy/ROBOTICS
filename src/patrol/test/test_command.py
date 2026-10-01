from patrol.patrol import command_from_pose
from turtlesim.msg import Pose


def test_missing_pose_is_zero():
    cmd = command_from_pose(None)
    assert cmd.linear.x == 0.0
    assert cmd.angular.z == 0.0


def test_normal_pose_returns_patrol():
    pose = Pose()
    pose.x = 5.0
    pose.y = 5.0
    pose.theta = 0.0
    cmd = command_from_pose(pose)
    assert cmd.linear.x == 0.5
    assert cmd.angular.z == 0.3
