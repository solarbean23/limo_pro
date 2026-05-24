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

    # setting for parameter
    namespace_name = robot_namespace()
    namespace = LaunchConfiguration('namespace')
    params_file = LaunchConfiguration('params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    container_name = LaunchConfiguration('container_name')
    container_name_full = (namespace, '/', container_name)
    scan_topic = f'/{namespace_name}/{topic_name("scan", "scan")}' if namespace_name else f'/{topic_name("scan", "scan")}'
 
    declare_namespace_cmd = DeclareLaunchArgument(
        'namespace',
        default_value=namespace_name,
        description='Top-level robot namespace')

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
        description='Automatically startup the navigation stack')

    declare_container_name_cmd = DeclareLaunchArgument(
        'container_name',
        default_value='nav2_container',
        description='Name of the component container')

    # Keep TF on the global /tf and /tf_static topics. The frame ids themselves
    # are already namespaced, and the rest of the robot stack publishes TF there.
    remappings = []
    
    # set the lifecycle nodes
    lifecycle_nodes = [
        'controller_server',
        'smoother_server',
        'planner_server',
        'behavior_server',
        'bt_navigator',
        'waypoint_follower',
        'velocity_smoother'
    ]

    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=params_file,
            root_key=namespace,
            param_rewrites={
                'use_sim_time': use_sim_time,
                'autostart': autostart,
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

    load_composable_nodes = GroupAction(
        actions=[
            LoadComposableNodes(
                target_container=container_name_full,
                composable_node_descriptions=[
                    ComposableNode( # loading controller server
                        package='nav2_controller',
                        plugin='nav2_controller::ControllerServer',
                        name='controller_server',
                        namespace=namespace,
                        parameters=[configured_params],
                        remappings=remappings + [('cmd_vel', 'cmd_vel_nav')]
                    ),
                    ComposableNode( # smoother server
                        package='nav2_smoother',
                        plugin='nav2_smoother::SmootherServer',
                        name='smoother_server',
                        namespace=namespace,
                        parameters=[configured_params],
                        remappings=remappings
                    ),
                    ComposableNode(
                        package='nav2_planner',
                        plugin='nav2_planner::PlannerServer',
                        name='planner_server',
                        namespace=namespace,
                        parameters=[configured_params],
                        remappings=remappings
                    ),
                    ComposableNode(
                        package='nav2_behaviors',
                        plugin='behavior_server::BehaviorServer',
                        name='behavior_server',
                        namespace=namespace,
                        parameters=[configured_params],
                        remappings=remappings
                    ),
                    ComposableNode(
                        package='nav2_bt_navigator',
                        plugin='nav2_bt_navigator::BtNavigator',
                        name='bt_navigator',
                        namespace=namespace,
                        parameters=[configured_params],
                        remappings=remappings
                    ),
                    ComposableNode(
                        package='nav2_waypoint_follower',
                        plugin='nav2_waypoint_follower::WaypointFollower',
                        name='waypoint_follower',
                        namespace=namespace,
                        parameters=[configured_params],
                        remappings=remappings
                    ),
                    ComposableNode(
                        package='nav2_velocity_smoother',
                        plugin='nav2_velocity_smoother::VelocitySmoother',
                        name='velocity_smoother',
                        namespace=namespace,
                        parameters=[configured_params],
                        remappings=remappings +
                            [('cmd_vel', 'cmd_vel_nav'), ('cmd_vel_smoothed', 'cmd_vel')]
                    ),
                    ComposableNode( # set the lifecycle manager
                        package='nav2_lifecycle_manager',
                        plugin='nav2_lifecycle_manager::LifecycleManager',
                        name='lifecycle_manager_navigation',
                        namespace=namespace,
                        parameters=[{
                            'use_sim_time': use_sim_time,
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
        declare_params_file_cmd,
        declare_use_sim_time_cmd,
        declare_autostart_cmd,
        declare_container_name_cmd,
        load_composable_nodes,
    ])
