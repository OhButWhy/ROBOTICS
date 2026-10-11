from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    record = LaunchConfiguration('record')
    bag_dir = LaunchConfiguration('bag_dir')
    subscriber_reliability = LaunchConfiguration('subscriber_reliability')

    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value='robot_a'),
        DeclareLaunchArgument('record', default_value='false'),
        DeclareLaunchArgument('bag_dir', default_value='evidence/pr05/bag'),
        DeclareLaunchArgument('subscriber_reliability',
                              default_value='best_effort'),

        Node(
            package='course_bringup',
            executable='pose_relay',
            namespace=namespace,
            output='screen',
            remappings=[('turtle1/pose', '/turtle1/pose')],
            parameters=[{'subscriber_reliability': subscriber_reliability}],
        ),

        ExecuteProcess(
            condition=IfCondition(record),
            cmd=['ros2', 'bag', 'record', '-s', 'mcap',
                 '-o', bag_dir,
                 '--topics', ['/', namespace, '/sensor_pose']],
            output='screen',
        ),
    ])
