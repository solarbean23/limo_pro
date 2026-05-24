import os
import sys
from launch import LaunchDescription
from launch.actions import GroupAction, DeclareLaunchArgument
from launch_ros.actions import LoadComposableNodes
from ament_index_python.packages import get_package_share_directory
from launch_ros.descriptions import ComposableNode, ParameterFile
from nav2_common.launch import RewrittenYaml
from launch.substitutions import LaunchConfiguration

wego_launch_dir = os.path.join(get_package_share_directory('wego'), 'launch')
if wego_launch_dir not in sys.path:
    sys.path.append(wego_launch_dir)

from _namespace_util import frame_name, robot_namespace, topic_name


def generate_launch_description():
    wego_share_dir = get_package_share_directory('wego_2d_nav')

    # setting for map and parameter
    namespace = LaunchConfiguration('namespace')
    map_yaml_file = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    container_name = LaunchConfiguration('container_name')
    container_name_full = (namespace, '/', container_name)
 
    declare_namespace_cmd = DeclareLaunchArgument(
        'namespace',
        default_value=robot_namespace(),
        description='Top-level robot namespace')

    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(wego_share_dir, 'maps', 'rescue_limo_1_map.yaml'),
        description='Full path to map yaml file to load')

    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(wego_share_dir, 'params', 'diff_navigation_params.yaml'),
        description='Full path to parameter yaml file to load')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock if true')

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically startup the localization stack')

    declare_container_name_cmd = DeclareLaunchArgument(
        'container_name',
        default_value='nav2_container',
        description='Name of the component container')

    # Keep TF on the global /tf and /tf_static topics. The frame ids themselves
    # are already namespaced, and the rest of the robot stack publishes TF there.
    remappings = []
    lifecycle_nodes = ['map_server', 'amcl']

    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=params_file,
            root_key=namespace,
            param_rewrites={
                'use_sim_time': use_sim_time,
                'yaml_filename': map_yaml_file,
                'base_frame_id': frame_name('base_link', 'base_link'),
                'odom_frame_id': frame_name('odom', 'odom'),
                'global_frame_id': frame_name('map', 'map'),
                'scan_topic': topic_name('scan', 'scan'),
            },
            convert_types=True,
        ),
        allow_substs=True,
    )

    load_composable_nodes = GroupAction(
        actions=[
            LoadComposableNodes(
                target_container=container_name_full,
                composable_node_descriptions=[
                    ComposableNode( # loading the map to map server
                        package='nav2_map_server',
                        plugin='nav2_map_server::MapServer',
                        name='map_server',
                        namespace=namespace,
                        parameters=[configured_params],
                        remappings=remappings,
                    ),
                    ComposableNode( # amcl localization
                        package='nav2_amcl',
                        plugin='nav2_amcl::AmclNode',
                        name='amcl',
                        namespace=namespace,
                        parameters=[configured_params],
                        remappings=remappings,
                    ),
                    ComposableNode( # For lifecycle
                        package='nav2_lifecycle_manager',
                        plugin='nav2_lifecycle_manager::LifecycleManager',
                        name='lifecycle_manager_localization',
                        namespace=namespace,
                        parameters=[
                            {'use_sim_time': use_sim_time,
                             'autostart': autostart,
                             'node_names': lifecycle_nodes}
                        ],
                    ),
                ],
            ),
        ],
    )
    
    return LaunchDescription([
        declare_namespace_cmd,
        declare_map_yaml_cmd,
        declare_params_file_cmd,
        declare_use_sim_time_cmd,
        declare_autostart_cmd,
        declare_container_name_cmd,
        load_composable_nodes,
    ])
