# Copyright 2018 Open Source Robotics Foundation, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from launch import LaunchDescription
import launch_ros.actions
import os
import sys
from ament_index_python.packages import get_package_share_directory
from launch_ros.descriptions import ParameterFile
from nav2_common.launch import RewrittenYaml

wego_launch_dir = os.path.join(get_package_share_directory('wego'), 'launch')
if wego_launch_dir not in sys.path:
    sys.path.append(wego_launch_dir)

from _namespace_util import frame_name, robot_namespace

def generate_launch_description():
    robot_localization_dir = get_package_share_directory('robot_localization')
    parameters_file_dir = os.path.join(robot_localization_dir, 'params')
    parameters_file_path = os.path.join(parameters_file_dir, 'limo_ekf.yaml')
    namespace = robot_namespace()
    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=parameters_file_path,
            root_key=namespace,
            param_rewrites={
                'odom_frame': frame_name('odom', 'odom'),
                'base_link_frame': frame_name('base_link', 'base_link'),
                'world_frame': frame_name('odom', 'odom'),
                'odom0': 'odom',
                'imu0': 'imu',
            },
            convert_types=True,
        ),
        allow_substs=True,
    )
    return LaunchDescription([
        # launch.actions.DeclareLaunchArgument(
        #     'output_final_position',
        #     default_value='false'),
        # launch.actions.DeclareLaunchArgument(
        #     'output_location',
	    # default_value='~/dual_ekf_navsat_example_debug.txt'),
	
    launch_ros.actions.Node(
            package='robot_localization', 
            executable='ekf_node', 
            name='ekf_filter_node_odom',
            namespace=namespace,
	        output='screen',
            parameters=[configured_params]
           )         
])
