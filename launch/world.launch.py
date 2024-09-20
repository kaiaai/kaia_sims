#!/usr/bin/env python3
#
# Copyright 2023-2024 KAIA.AI, REMAKE.AI
#
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

import os, re
from ament_index_python.packages import get_package_share_path
from launch import LaunchDescription, LaunchContext
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.actions import Node
from kaiaai import config


def make_nodes(context: LaunchContext, robot_model, use_sim_time, x_pose, y_pose, world):
    robot_model_str = context.perform_substitution(robot_model)
    use_sim_time_str = context.perform_substitution(use_sim_time)
    x_pose_str = context.perform_substitution(x_pose)
    y_pose_str = context.perform_substitution(y_pose)
    world_str = context.perform_substitution(world)

    if len(robot_model_str) == 0:
      robot_model_str = config.get_var('robot.model')

    urdf_path_name = os.path.join(
      get_package_share_path(robot_model_str),
      'urdf',
      'robot.urdf.xacro')

    robot_description = ParameterValue(Command(['xacro ', urdf_path_name]), value_type=str)

    sdf_path_name = os.path.join(
        get_package_share_path(robot_model_str),
        'sdf',
        robot_model_str,
        'model.sdf'
    )

    pkg_gazebo_ros = get_package_share_path('gazebo_ros')
    world_path_name = os.path.join(get_package_share_path('kaiaai_gazebo'), 'worlds', world_str)

    print('URDF  file name : {}'.format(urdf_path_name))
    print('SDF   file name : {}'.format(sdf_path_name))
    print('World file name : {}'.format(world_path_name))

    return [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')
            ),
            launch_arguments={'world': world_path_name}.items()
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time_str.lower() == 'true',
                'robot_description': robot_description
            }]
        ),
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=[
                '-entity', robot_model_str,
                '-file', sdf_path_name,
                '-timeout', '180',
                '-x', x_pose_str,
                '-y', y_pose_str,
                '-z', '0.01'
            ],
            output='screen'
        )
    ]

def generate_launch_description():

    pkg_gazebo_ros = get_package_share_path('gazebo_ros')

    return LaunchDescription([
        DeclareLaunchArgument(
            name='use_sim_time',
            default_value='true',
            choices=['true', 'false'],
            description='Use simulation (Gazebo) clock if true'
        ),
        DeclareLaunchArgument(
            name='robot_model',
            default_value='',
            description='Robot description package name'
        ),
        DeclareLaunchArgument(
            name='x_pose',
            default_value='-2.0',
            description='Robot starting x position'
        ),
        DeclareLaunchArgument(
            name='y_pose',
            default_value='-0.5',
            description='Robot starting y position'
        ),
        DeclareLaunchArgument(
            name='world',
            default_value='living_room.world',
            description='World file name'
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')
            ),
        ),
        OpaqueFunction(function=make_nodes, args=[
            LaunchConfiguration('robot_model'),
            LaunchConfiguration('use_sim_time'),
            LaunchConfiguration('x_pose'),
            LaunchConfiguration('y_pose'),
            LaunchConfiguration('world')
        ])
    ])
