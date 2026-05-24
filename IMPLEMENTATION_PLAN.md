# Limo namespace 기반 Mapping / Navigation 구현 계획

## 1. 이번 단계의 목표

지금 목표는 `Rescue_Limo_1` 한 대를 먼저 안정화하는 것이다.

1. `Rescue_Limo_1` namespace와 TF prefix가 적용된 상태로 LIMO bringup
2. 같은 namespace 상태에서 mapping 실행
3. map 저장
4. 저장한 map으로 AMCL + Nav2 navigation 검증
5. 그 다음에만 py_bt_ros 연동 검증

중요한 제한:

- `/home/wego/workspace/py_bt_ros`는 아직 수정하지 않는다.
- py_bt_ros 안의 Limo adapter는 나중에 제거할 방향이다.
- pose bridge나 world_manager가 필요하면 우선 wego_ws 쪽 별도 노드/패키지로 두는 방향을 우선 검토한다.
- 새 Nav2 action server를 만들지 않는다. py_bt_ros는 최종적으로 각 로봇의 `/<ns>/navigate_to_pose`에 goal만 보낸다.

## 2. namespace와 TF의 기본 규칙

ROS topic/action/service/node namespace와 TF frame prefix는 별도로 생각한다.

### 공유하는 것

| 항목 | 이름 |
|---|---|
| global frame | `map` |
| 저장된 map 파일 | `map.yaml`, `map.pgm` |
| TF 토픽 | `/tf`, `/tf_static` |
| 협업 토픽 | `/world/...`, `/agent/alive`, `/agent_broadcast`, `/metrics/...` |

`map` frame은 prefix를 붙이지 않는다. 모든 로봇이 같은 지도 좌표계에서 움직여야 하기 때문이다.

### 로봇마다 분리하는 것

| 항목 | 예시 |
|---|---|
| base command | `/Rescue_Limo_1/cmd_vel` |
| raw odom | `/Rescue_Limo_1/odom` |
| imu | `/Rescue_Limo_1/imu` |
| scan | `/Rescue_Limo_1/scan` |
| filtered odom | `/Rescue_Limo_1/odometry/filtered` |
| AMCL pose | `/Rescue_Limo_1/amcl_pose` |
| initial pose | `/Rescue_Limo_1/initialpose` |
| Nav2 action | `/Rescue_Limo_1/navigate_to_pose` |

### 목표 TF tree

현재 diff xacro는 `base_footprint`보다 `base_link` 중심이므로, 1차 목표는 실제 파일 구조에 맞춘다.

```text
map
└── Rescue_Limo_1/odom
    └── Rescue_Limo_1/base_link
        ├── Rescue_Limo_1/laser_link
        ├── Rescue_Limo_1/imu_link
        └── Rescue_Limo_1/..._wheel_link
```

나중에 `base_footprint`가 꼭 필요하면 URDF에 명시적으로 추가한다. 지금 단계에서는 없는 frame을 계획에 먼저 넣지 않는다.

## 3. 단일 source of truth

`wego/config/namespace.yaml`을 각 LIMO host의 유일한 robot identity 파일로 둔다.

```yaml
robot:
  namespace: Rescue_Limo_1
  type: Rescue_Limo
  leader_priority: 0

frames:
  map: map
  odom: odom
  base_link: base_link
  laser: laser_link
  imu: imu_link

topics:
  cmd_vel: cmd_vel
  odom_raw: odom
  imu: imu
  scan: scan
  odom_filtered: odometry/filtered
```

launch helper는 이 파일을 읽어서 아래 값을 만든다.

```text
namespace       = Rescue_Limo_1
odom_frame      = Rescue_Limo_1/odom
base_link_frame = Rescue_Limo_1/base_link
laser_frame     = Rescue_Limo_1/laser_link
imu_frame       = Rescue_Limo_1/imu_link
```

토픽은 가능하면 relative name을 쓴다. 예를 들어 node가 `namespace=Rescue_Limo_1` 안에서 `scan`을 publish하면 최종 토픽은 `/Rescue_Limo_1/scan`이 된다.

절대 토픽(`/scan`, `/cmd_vel`, `/odom`, `/odometry/filtered`)은 namespace를 우회하므로 제거하거나 launch에서 명시적으로 rewrite한다.

## 4. Phase 1 - namespace helper와 build 범위 정리

### 변경할 것

- `wego/launch/_namespace_util.py` 신설
  - `wego/config/namespace.yaml` 로딩
  - namespace normalize
  - TF frame prefix 생성
  - 필요하면 `RewrittenYaml` param rewrite dictionary 생성

### build 전략

처음부터 전체 workspace를 빌드하지 않는다. 특히 `navigation2` 전체를 건드리지 않는다.

우선 대상:

```bash
colcon build --symlink-install --packages-select \
  wego \
  limo_base \
  limo_description \
  ydlidar_ros2_driver \
  robot_localization \
  wego_2d_nav
```

`robot_localization`이나 `ydlidar_ros2_driver`에서 build 문제가 나면 한 패키지씩 분리해서 본다.

```bash
colcon build --symlink-install --packages-select ydlidar_ros2_driver
colcon build --symlink-install --packages-select robot_localization
```

launch/params만 바꾼 패키지는 `--symlink-install`이면 반복 검증이 편하다.

## 5. Phase 2 - base driver, lidar, robot_state_publisher namespacing

### limo_base

수정 대상:

- `limo_ros2/limo_base/src/limo_driver.cpp`
- `limo_ros2/limo_base/src/limo_ackerman_driver.cpp`
- `limo_ros2/limo_base/launch/limo_base.launch.py`

해야 할 일:

- publisher/subscriber의 절대 토픽 제거
  - `/cmd_vel` -> `cmd_vel`
  - `/odom` -> `odom` 또는 `odom_topic_name` param
  - `/imu` -> `imu`
  - `/limo_status` -> `limo_status`
- `odom_frame`, `base_frame`, `imu_frame`을 namespace prefix가 붙은 값으로 launch에서 전달
  - `Rescue_Limo_1/odom`
  - `Rescue_Limo_1/base_link`
  - `Rescue_Limo_1/imu_link`
- node namespace를 `Rescue_Limo_1`로 설정
- `namespace='limo'` 하드코딩 제거

검증:

```bash
ros2 topic list | grep Rescue_Limo_1
ros2 topic echo /Rescue_Limo_1/odom
ros2 topic echo /Rescue_Limo_1/imu
```

### ydlidar

수정 대상:

- `ydlidar_ros2_driver/launch/ydlidar.launch.py`
- `ydlidar_ros2_driver/params/ydlidar.yaml`

해야 할 일:

- driver node namespace를 `Rescue_Limo_1`로 설정
- scan topic이 relative `scan`으로 publish되는지 확인
- `frame_id`를 `Rescue_Limo_1/laser_link`로 rewrite
- `laser_link`와 `laser_frame` 혼용 제거
- URDF가 `laser_link` fixed joint를 publish한다면 별도 static transform publisher는 중복으로 띄우지 않는다.

검증:

```bash
ros2 topic echo /Rescue_Limo_1/scan
```

### robot_state_publisher / URDF

수정 대상:

- `limo_ros2/limo_description/urdf/limo_four_diff.xacro`
- `limo_ros2/limo_description/urdf/limo_xacro.xacro`
- `limo_ros2/limo_description/launch/load_urdf.launch.py`

해야 할 일:

- xacro에 `tf_prefix` 또는 `frame_prefix` 인자를 추가
- 모든 link/joint frame 이름이 `Rescue_Limo_1/...` 형태가 되도록 구성
- `robot_state_publisher`도 namespace 안에 두되, TF frame 이름 prefix는 URDF 자체에서 해결

검증:

```bash
ros2 run tf2_tools view_frames
ros2 run tf2_ros tf2_echo Rescue_Limo_1/base_link Rescue_Limo_1/laser_link
ros2 run tf2_ros tf2_echo Rescue_Limo_1/base_link Rescue_Limo_1/imu_link
```

## 6. Phase 3 - robot_localization namespacing

수정 대상:

- `robot_localization/launch/limo_ekf_launch.py`
- `robot_localization/params/limo_ekf.yaml`

해야 할 일:

- EKF node namespace를 `Rescue_Limo_1`로 설정
- input topics는 relative로 유지
  - `odom0: odom`
  - `imu0: imu`
- output topic은 relative `odometry/filtered`
- frame params는 prefix 적용
  - `odom_frame: Rescue_Limo_1/odom`
  - `base_link_frame: Rescue_Limo_1/base_link`
  - `world_frame: Rescue_Limo_1/odom`
- 가능하면 원본 yaml을 robot별로 복사하지 않고 launch에서 `RewrittenYaml`로 rewrite한다.

검증:

```bash
ros2 topic echo /Rescue_Limo_1/odometry/filtered
ros2 run tf2_ros tf2_echo Rescue_Limo_1/odom Rescue_Limo_1/base_link
```

주의:

- `robot_localization`이 `/odom`이나 `/imu`를 보고 있으면 실패다.
- `/Rescue_Limo_1/odom`, `/Rescue_Limo_1/imu`를 input으로 받아야 한다.

## 7. Phase 4 - namespace 적용 상태로 mapping

수정 대상:

- `wego/launch/cartographer_launch.py`
- `wego/launch/occupancy_grid_launch.py`
- `wego/config/limo_lds_2d.lua`

해야 할 일:

- cartographer node namespace를 `Rescue_Limo_1`로 설정
- cartographer input topic은 namespace 안의 relative topic을 사용
  - `scan`
  - `odometry/filtered`
- lua frame 값을 prefix 적용
  - `map_frame = "map"`
  - `tracking_frame = "Rescue_Limo_1/imu_link"` 또는 검증 후 `Rescue_Limo_1/base_link`
  - `published_frame = "Rescue_Limo_1/odom"`
  - `odom_frame = "Rescue_Limo_1/odom"`
- occupancy grid는 우선 `/Rescue_Limo_1/map`으로 publish되게 둔다.
- map 저장 시 topic을 명시한다.

실행 흐름:

```bash
ros2 launch limo_description load_urdf.launch.py
ros2 launch limo_base limo_base.launch.py
ros2 launch ydlidar_ros2_driver ydlidar.launch.py
ros2 launch robot_localization limo_ekf_launch.py
ros2 launch wego cartographer_launch.py
```

검증:

```bash
ros2 topic echo /Rescue_Limo_1/scan
ros2 topic echo /Rescue_Limo_1/odometry/filtered
ros2 topic echo /Rescue_Limo_1/map
ros2 run tf2_ros tf2_echo map Rescue_Limo_1/base_link
```

map 저장:

```bash
ros2 run nav2_map_server map_saver_cli \
  -t /Rescue_Limo_1/map \
  -f /home/wego/wego_ws/src/wego_2d_nav/maps/rescue_limo_1_map
```

저장 후 `rescue_limo_1_map.yaml`, `rescue_limo_1_map.pgm`을 navigation에서 사용한다.

## 8. Phase 5 - 저장한 map으로 navigation 검증

수정 대상:

- `wego/launch/navigation_diff_launch.py`
- `wego_2d_nav/launch/localization_launch.py`
- `wego_2d_nav/launch/navigation_only_launch.py`
- `wego_2d_nav/params/diff_navigation_params.yaml`

해야 할 일:

- Nav2 container와 composable nodes를 `Rescue_Limo_1` namespace 안에 둔다.
- `target_container` 이름이 namespaced container를 정확히 가리키는지 확인한다.
- AMCL frame params rewrite
  - `base_frame_id: Rescue_Limo_1/base_link`
  - `odom_frame_id: Rescue_Limo_1/odom`
  - `global_frame_id: map`
  - `scan_topic: scan`
- BT navigator / costmap / behavior params rewrite
  - `robot_base_frame: Rescue_Limo_1/base_link`
  - `global_frame: map`
  - `local_frame` 또는 local costmap `global_frame: Rescue_Limo_1/odom`
  - `odom_topic: odometry/filtered`
  - scan topic은 `scan`, 절대 `/scan` 금지
- cmd_vel remap은 relative name을 유지해서 최종적으로 `/Rescue_Limo_1/cmd_vel`로 나가게 한다.

검증:

```bash
ros2 action list | grep Rescue_Limo_1
ros2 topic list | grep Rescue_Limo_1
ros2 lifecycle nodes
ros2 run tf2_ros tf2_echo map Rescue_Limo_1/base_link
```

RViz goal 검증:

- Fixed Frame: `map`
- 2D Pose Estimate topic: `/Rescue_Limo_1/initialpose`
- Nav2 Goal action/topic: `/Rescue_Limo_1/navigate_to_pose`

## 9. 여러 로봇이 같은 map을 사용할 때

mapping은 한 로봇으로 한 번만 수행한다. 이후 여러 로봇은 같은 map 파일을 복사해서 사용한다.

각 로봇은 자기 namespace로 전체 stack을 띄운다.

```text
Rescue_Limo_1:
  /Rescue_Limo_1/scan
  /Rescue_Limo_1/odometry/filtered
  /Rescue_Limo_1/amcl_pose
  /Rescue_Limo_1/navigate_to_pose
  TF: map -> Rescue_Limo_1/odom -> Rescue_Limo_1/base_link

Fire_Limo_1:
  /Fire_Limo_1/scan
  /Fire_Limo_1/odometry/filtered
  /Fire_Limo_1/amcl_pose
  /Fire_Limo_1/navigate_to_pose
  TF: map -> Fire_Limo_1/odom -> Fire_Limo_1/base_link
```

각 로봇은 자체 AMCL을 사용한다. 같은 map 파일을 보더라도 initial pose는 로봇마다 따로 넣어야 한다.

## 10. 2D Pose Estimate는 어디서 하는가?

반드시 각 LIMO 화면에서 해야 하는 것은 아니다.

가능한 방식:

1. 운영 노트북 RViz 하나에서 로봇별로 initial pose topic을 바꿔가며 넣기
   - `/Rescue_Limo_1/initialpose`
   - `/Fire_Limo_1/initialpose`
   - `/Fire_Limo_2/initialpose`
2. 각 LIMO 화면의 RViz에서 자기 robot namespace의 initial pose topic으로 넣기
3. CLI로 직접 publish하기

운영 노트북이 같은 `ROS_DOMAIN_ID`와 DDS network 안에 있으면, 운영 노트북 RViz에서 모든 LIMO의 initial pose를 줄 수 있다. 이 방식이 여러 로봇 운용에서는 더 깔끔하다.

중요한 점:

- global `/initialpose`로 보내면 안 된다.
- RViz의 2D Pose Estimate tool topic을 로봇별 namespace로 바꿔야 한다.
- goal도 마찬가지로 `/Rescue_Limo_1/navigate_to_pose`처럼 로봇별 action에 보내야 한다.

예시:

```bash
ros2 topic pub --once /Rescue_Limo_1/initialpose \
  geometry_msgs/msg/PoseWithCovarianceStamped "{header: {frame_id: map}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}"
```

## 11. py_bt_ros 연동은 navigation 검증 후

navigation이 안정화되기 전에는 py_bt_ros를 수정하지 않는다.

최종 방향:

- 운영 노트북은 SSH로 각 LIMO에서 `python3 main.py --config=...`를 실행시킨다.
- BT runner는 각 LIMO에서 실행된다.
- 각 config는 자기 namespace를 가진다.
  - `/Rescue_Limo_1`
  - `/Fire_Limo_1`
  - `/Fire_Limo_2`
- py_bt_ros는 각 robot의 Nav2 action `/<ns>/navigate_to_pose`에 goal을 보낸다.
- `/world/...` target/base 정보는 운영 노트북의 world_manager가 global topic/service로 제공한다.
- `/<ns>/pose_world`가 필요하면 py_bt_ros 내부 adapter가 아니라 wego_ws 쪽 bridge node에서 제공하는 방향을 우선 검토한다.

## 12. 최종 검증 체크리스트

### 단일 LIMO bringup

```bash
ros2 topic list | grep Rescue_Limo_1
ros2 topic echo /Rescue_Limo_1/scan
ros2 topic echo /Rescue_Limo_1/odom
ros2 topic echo /Rescue_Limo_1/imu
ros2 topic echo /Rescue_Limo_1/odometry/filtered
```

### TF

```bash
ros2 run tf2_tools view_frames
ros2 run tf2_ros tf2_echo Rescue_Limo_1/base_link Rescue_Limo_1/laser_link
ros2 run tf2_ros tf2_echo Rescue_Limo_1/odom Rescue_Limo_1/base_link
```

### Mapping

```bash
ros2 topic echo /Rescue_Limo_1/map
ros2 run tf2_ros tf2_echo map Rescue_Limo_1/base_link
ros2 run nav2_map_server map_saver_cli -t /Rescue_Limo_1/map -f /home/wego/wego_ws/src/wego_2d_nav/maps/rescue_limo_1_map
```

### Navigation

```bash
ros2 action list | grep navigate_to_pose
ros2 topic echo /Rescue_Limo_1/amcl_pose
ros2 run tf2_ros tf2_echo map Rescue_Limo_1/base_link
```

RViz에서:

- Fixed Frame: `map`
- Initial Pose: `/Rescue_Limo_1/initialpose`
- Nav2 Goal: `/Rescue_Limo_1/navigate_to_pose`

## 13. 지금 의식적으로 하지 않는 것

- py_bt_ros 수정
- py_bt_ros 안에 Limo adapter 추가
- 새 Nav2 action server 작성
- global `/cmd_vel`, `/scan`, `/odom`, `/initialpose` 사용
- `map` frame에 robot prefix 붙이기
- 여러 로봇 동시 실행
- navigation 검증 전에 world_manager/mission BT까지 한 번에 붙이기
