import os
import sys
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

from launch_ros.descriptions import ParameterFile
from nav2_common.launch import RewrittenYaml

wego_launch_dir = os.path.join(get_package_share_directory('wego'), 'launch')
if wego_launch_dir not in sys.path:
    sys.path.append(wego_launch_dir)

from _namespace_util import frame_name, robot_namespace, topic_name


def generate_launch_description():
    wego_share_dir = get_package_share_directory('wego')
    wego_nav_share_dir = get_package_share_directory('wego_2d_nav')
    namespace = robot_namespace()
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    container_name = 'nav2_container'
    scan_topic = f'/{namespace}/{topic_name("scan", "scan")}' if namespace else f'/{topic_name("scan", "scan")}'

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock if true')

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically startup the Nav2 stack')

    # setting for rviz configuration path
    rviz_file_name = 'navigation.rviz'
    rviz_config_path = os.path.join(wego_share_dir, 'rviz', rviz_file_name)

    # set the parameters
    parameter_file_name = 'diff_navigation_params.yaml'
    parameter_file_path = os.path.join(wego_nav_share_dir, 'params', parameter_file_name)

    # set the map yaml file
    map_file_name = 'my_map.yaml'
    map_file_path = os.path.join(wego_nav_share_dir, 'maps', map_file_name)

    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=parameter_file_path,
            root_key=namespace,
            param_rewrites={
                'use_sim_time': use_sim_time,
                'autostart': autostart,
                'yaml_filename': map_file_path,
                'base_frame_id': frame_name('base_link', 'base_link'),
                'odom_frame_id': frame_name('odom', 'odom'),
                'global_frame_id': frame_name('map', 'map'),
                'robot_base_frame': frame_name('base_link', 'base_link'),
                'local_frame': frame_name('odom', 'odom'),
                'odom_topic': topic_name('odom_filtered', 'odometry/filtered'),
                'local_costmap.local_costmap.ros__parameters.global_frame': frame_name('odom', 'odom'),
                'local_costmap.local_costmap.ros__parameters.obstacle_layer.scan.topic': scan_topic,
                'global_costmap.global_costmap.ros__parameters.obstacle_layer.scan.topic': scan_topic,
            },
            convert_types=True,
        ),
        allow_substs=True,
    )

    # set container for composable node
    nav2_container = Node(
        name=container_name,
        package='rclcpp_components',
        executable='component_container_isolated',
        namespace=namespace,
        parameters=[configured_params, {'autostart': autostart}],
        arguments=['--ros-args', '--log-level', 'info'],
        output='screen',
    )

    # For localization
    localization_launch = IncludeLaunchDescription(
        PathJoinSubstitution([
            FindPackageShare('wego_2d_nav'),
            'launch', 
            'localization_launch.py',
        ]),
        launch_arguments={
            'map' : map_file_path,
            'params_file': parameter_file_path,
            'namespace': namespace,
            'container_name': container_name,
            'use_sim_time': use_sim_time,
            'autostart': autostart,
        }.items()
    )

    # For navigation
    navigation_launch = IncludeLaunchDescription(
        PathJoinSubstitution([
            FindPackageShare('wego_2d_nav'),
            'launch',
            'navigation_only_launch.py',
        ]),
        launch_arguments={
            'params_file': parameter_file_path,
            'namespace': namespace,
            'container_name': container_name,
            'use_sim_time': use_sim_time,
            'autostart': autostart,
        }.items()
    )

    # setting for rviz
    rviz_config_node = Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            namespace=namespace,
            output='screen',
            arguments=['-d', rviz_config_path],
        )

    return LaunchDescription([
        declare_use_sim_time_cmd,
        declare_autostart_cmd,
        nav2_container,
        localization_launch,
        navigation_launch,
        rviz_config_node,
    ])
