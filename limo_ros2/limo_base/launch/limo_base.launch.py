import launch
import launch_ros
import os
import sys

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

wego_launch_dir = os.path.join(get_package_share_directory('wego'), 'launch')
if wego_launch_dir not in sys.path:
    sys.path.append(wego_launch_dir)

from _namespace_util import frame_name, robot_namespace, topic_name


def generate_launch_description():
    namespace_config = None
    namespace = robot_namespace(namespace_config)
    odom_frame = frame_name('odom', 'odom', namespace_config)
    base_frame = frame_name('base_link', 'base_link', namespace_config)
    imu_frame = frame_name('imu', 'imu_link', namespace_config)
    odom_topic = topic_name('odom_raw', 'odom', namespace_config)

    # use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='false',
    #                                          description='Use simulation clock if true')

    port_name_arg = DeclareLaunchArgument('port_name', default_value='ttylimo',
                                         description='usb bus name, e.g. ttyUSB0')
    odom_frame_arg = DeclareLaunchArgument('odom_frame', default_value=odom_frame,
                                           description='Odometry frame id')
    base_link_frame_arg = DeclareLaunchArgument('base_frame', default_value=base_frame,
                                                description='Base link frame id')
    imu_frame_arg = DeclareLaunchArgument('imu_frame', default_value=imu_frame,
                                          description='IMU frame id')
    odom_topic_arg = DeclareLaunchArgument('odom_topic_name', default_value=odom_topic,
                                           description='Odometry topic name')
    odom_tf_arg = DeclareLaunchArgument('pub_odom_tf', default_value='False',
                                           description='Odometry topic name')

    # is_scout_mini_arg = DeclareLaunchArgument('is_scout_mini', default_value='false',
    #                                       description='Scout mini model')
    # is_omni_wheel_arg = DeclareLaunchArgument('is_omni_wheel', default_value='false',
    #                                       description='Scout mini omni-wheel model')

    # simulated_robot_arg = DeclareLaunchArgument('simulated_robot', default_value='false',
    #                                                description='Whether running with simulator')
    sim_control_rate_arg = DeclareLaunchArgument('control_rate', default_value='50',
                                                 description='Simulation control loop update rate')
    
    limo_base_node = launch_ros.actions.Node(
        package='limo_base',
        executable='limo_base',  #foxy executable='limo_base',
        output='screen',
        emulate_tty=True,
        parameters=[{
                # 'use_sim_time': launch.substitutions.LaunchConfiguration('use_sim_time'),
                'port_name': launch.substitutions.LaunchConfiguration('port_name'),                
                'odom_frame': launch.substitutions.LaunchConfiguration('odom_frame'),
                'base_frame': launch.substitutions.LaunchConfiguration('base_frame'),
                'imu_frame': launch.substitutions.LaunchConfiguration('imu_frame'),
                'odom_topic_name': launch.substitutions.LaunchConfiguration('odom_topic_name'),
                'pub_odom_tf': launch.substitutions.LaunchConfiguration('pub_odom_tf'),
                'control_rate': launch.substitutions.LaunchConfiguration('control_rate'),
        }],
        namespace=namespace,
    )

    return LaunchDescription([
        # use_sim_time_arg,
        port_name_arg,        
        odom_frame_arg,
        base_link_frame_arg,
        imu_frame_arg,
        odom_topic_arg,
        odom_tf_arg,
        # is_scout_mini_arg,
        # is_omni_wheel_arg,
        # simulated_robot_arg,
        sim_control_rate_arg,
        limo_base_node
    ])
