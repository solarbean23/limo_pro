from ament_index_python.packages import get_package_share_path
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import os
import sys

wego_launch_dir = os.path.join(get_package_share_directory('wego'), 'launch')
if wego_launch_dir not in sys.path:
    sys.path.append(wego_launch_dir)

from _namespace_util import robot_namespace, tf_prefix

def generate_launch_description():
    urdf_tutorial_path = get_package_share_path('limo_description')
    default_model_path = urdf_tutorial_path / 'urdf/limo_four_diff.xacro'
    namespace = robot_namespace()
    prefix = tf_prefix()

    model_arg = DeclareLaunchArgument(name='model', default_value=str(default_model_path),
                                      description='Absolute path to robot urdf file')

    robot_description = ParameterValue(
        Command(['xacro ', LaunchConfiguration('model'), ' tf_prefix:=', prefix]),
        value_type=str
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace=namespace,
        parameters=[{'robot_description': robot_description}]
    )

    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        namespace=namespace,
    )

    return LaunchDescription([
        model_arg,
        joint_state_publisher_node,
        robot_state_publisher_node,
    ])
