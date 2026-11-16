import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, ExecuteProcess, SetEnvironmentVariable
)
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_course_sim = get_package_share_directory('course_simulation')
    pkg_course_desc = get_package_share_directory('course_description')

    world = LaunchConfiguration('world')
    bridge_config = LaunchConfiguration('bridge_config')
    headless = LaunchConfiguration('headless')

    xacro_file = os.path.join(pkg_course_desc, 'urdf', 'vehicle.urdf.xacro')
    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]), value_type=str)

    models_path = os.path.join(pkg_course_sim, 'models')

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=os.path.join(pkg_course_sim, 'worlds', 'mcity-minimal.sdf')
        ),
        DeclareLaunchArgument(
            'bridge_config',
            default_value=os.path.join(pkg_course_sim, 'config', 'bridge.yaml')
        ),
        DeclareLaunchArgument('headless', default_value='true'),

        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', models_path),

        # Запуск Gazebo в headless режиме (с рендерингом без окна)
        ExecuteProcess(
            condition=IfCondition(headless),
            cmd=['gz', 'sim', '-r', '-s', '--headless-rendering', world],
            output='screen'
        ),
        # Запуск Gazebo с графическим окном (если headless:=false)
        ExecuteProcess(
            condition=UnlessCondition(headless),
            cmd=['gz', 'sim', '-r', world],
            output='screen'
        ),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
            output='screen'
        ),

        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{'config_file': bridge_config, 'use_sim_time': True}],
            output='screen'
        ),

        Node(
            package='course_simulation',
            executable='ackermann_adapter',
            parameters=[{'use_sim_time': True}],
            output='screen'
        ),
        Node(
            package='course_simulation',
            executable='odom_adapter',
            parameters=[{'use_sim_time': True}],
            output='screen'
        )
    ])
