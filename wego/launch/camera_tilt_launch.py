import os
import sys

import launch

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

from launch.actions import DeclareLaunchArgument

from launch.substitutions import LaunchConfiguration

wego_launch_dir = os.path.join(get_package_share_directory('wego'), 'launch')
if wego_launch_dir not in sys.path:
    sys.path.append(wego_launch_dir)

from _namespace_util import frame_name, robot_namespace


def generate_launch_description():
    degree = LaunchConfiguration('degree')
    namespace = robot_namespace()
    camera_prefix = f'{namespace}_camera' if namespace else 'camera'
    camera_mount_frame = f'{camera_prefix}_mount'
    camera_rotate_frame = f'{camera_prefix}_rotate'
    camera_link_frame = f'{camera_prefix}_link'

    degree_launch_arg = DeclareLaunchArgument(
        'degree',
        default_value='0.0'
    )

    return launch.LaunchDescription([
        degree_launch_arg,
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_camera_mount',
            namespace=namespace,
            arguments=[
                '--x', '0.2',
                '--y', '0.1',
                '--z', '0.06',
                '--yaw', '0',
                '--pitch', '0',
                '--roll', '0',
                '--frame-id', frame_name('base_link', 'base_link'),
                '--child-frame-id', camera_mount_frame,
            ],
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='camera_mount_to_roate',
            namespace=namespace,
            arguments=[
                '--x', '0.00',
                '--y', '0.00',
                '--z', '0.00',
                '--yaw', '0',
                '--pitch', degree,
                '--roll', '0',
                '--frame-id', camera_mount_frame,
                '--child-frame-id', camera_rotate_frame,
            ],
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='rotate_to_camera_link',
            namespace=namespace,
            arguments=[
                '--x', '0.03',
                '--y', '-0.05',
                '--z', '0.00',
                '--yaw', '0',
                '--pitch', '0',
                '--roll', '0',
                '--frame-id', camera_rotate_frame,
                '--child-frame-id', camera_link_frame,
            ],
        )
    ])
