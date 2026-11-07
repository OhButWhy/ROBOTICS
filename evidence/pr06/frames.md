# PR06 — Дерево трансформаций

## Владельцы преобразований
Все статические преобразования публикует единственная нода `/robot_state_publisher`.

## Статические (fixed) — в /tf_static

| Parent | Child | Type | Offset (x y z) | Владелец публикации |
|---|---|---|---|---|
| base_link | camera_link | fixed | 0.40 0.00 0.25 | robot_state_publisher |
| base_link | lidar_link  | fixed | 0.00 0.00 0.31 | robot_state_publisher |
| base_link | imu_link    | fixed | 0.00 0.00 0.12 | robot_state_publisher |

## Динамические (не публикуются без /joint_states)

| Parent | Child | Type | Владелец публикации |
|---|---|---|---|
| base_link | front_left_knuckle | revolute Z | (нет источника joint_states) |
| base_link | front_right_knuckle | revolute Z | (нет источника joint_states) |
| front_left_knuckle | front_left_wheel | continuous Y | (нет источника joint_states) |
| front_right_knuckle | front_right_wheel | continuous Y | (нет источника joint_states) |
| base_link | rear_left_wheel | continuous Y | (нет источника joint_states) |
| base_link | rear_right_wheel | continuous Y | (нет источника joint_states) |

*Примечание: колеса не публикуются, так как в образе нет `joint_state_publisher`. Для сдачи обязательной части это не требуется.*

## Проверка одной связи (tf2_echo)
```text
$ ros2 run tf2_ros tf2_echo base_link lidar_link
At time 0.0
- Translation: [0.000, 0.000, 0.310]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
