import os
import sys
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import ThisLaunchFileDir

wego_launch_dir = os.path.join(get_package_share_directory('wego'), 'launch')
if wego_launch_dir not in sys.path:
    sys.path.append(wego_launch_dir)

from _namespace_util import namespace_env, robot_namespace


def generate_launch_description():
    wego_share_dir = get_package_share_directory('wego')
    namespace = robot_namespace()
    cartographer_config_dir = LaunchConfiguration('cartographer_config_dir',
                                    default=os.path.join(wego_share_dir, 'config'))
    configuration_file = LaunchConfiguration('configuration_file', default='limo_lds_2d.lua')

    resolution = LaunchConfiguration('resolution', default='0.05')
    publish_period_sec = LaunchConfiguration('publish_period_sec', default='1.0')

    rviz_config_dir = os.path.join(get_package_share_directory('wego'), 'rviz', 'cartographer.rviz')

    return LaunchDescription([
        DeclareLaunchArgument(
            'cartographer_config_dir',
            default_value=cartographer_config_dir,
            description='Full path to config file to load'),
        DeclareLaunchArgument(
            'configuration_file',
            default_value=configuration_file,
            description='Name of lua file for cartographer'),
        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            remappings=[('odom','odometry/filtered'),],
            namespace=namespace,
            additional_env=namespace_env(),
            output='screen',
            arguments=['-configuration_directory', cartographer_config_dir,
                       '-configuration_basename', configuration_file]),

        DeclareLaunchArgument(
            'resolution',
            default_value=resolution,
            description='Resolution of a grid cell in the published occupancy grid'),

        DeclareLaunchArgument(
            'publish_period_sec',
            default_value=publish_period_sec,
            description='OccupancyGrid publishing period'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([ThisLaunchFileDir(), '/occupancy_grid_launch.py']),
            launch_arguments={'resolution': resolution,
                              'publish_period_sec': publish_period_sec}.items(),
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_dir],
            output='screen'),
    ])
