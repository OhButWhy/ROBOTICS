# ROBOTICS — практические работы

Репозиторий с лабораторными работами курса. Каждая ПР — отдельная папка
в `evidence/<PR_ID>/`, исходный код — в `src/`.

- **PR01** — базовый граф ROS 2 (turtlesim + teleop), разрыв по `ROS_DOMAIN_ID`.
- **PR02** — пакет `turtle_bringup`, launch-файл, CLI-доставка команды.

## Среда

- ROS 2: **jazzy** (`source /opt/ros/jazzy/setup.bash`)
- Домен: `ROS_DOMAIN_ID=16`
- Workspace: корень этого репозитория
- Запуск: WSL2 (Ubuntu 24.04) либо Docker-образ `osrf/ros:jazzy-desktop-full`

## PR01 — порядок запуска

Три терминала A/B/C, в каждом:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=16
cd "$(git rev-parse --show-toplevel)"
```

Терминал A — симулятор:

```bash
ros2 run turtlesim turtlesim_node
```

Терминал B — управление (фокус оставить здесь, стрелками двигать черепаху):

```bash
ros2 run turtlesim turtle_teleop_key
```

Терминал C — сбор улик:

```bash
mkdir -p evidence/pr01
ros2 doctor --report                > evidence/pr01/doctor.txt 2>&1
ros2 node list --no-daemon --spin-time 2 > evidence/pr01/nodes-before.txt
ros2 topic list -t                  > evidence/pr01/topics.txt
ros2 node info /turtlesim           > evidence/pr01/turtlesim-info.txt
ros2 node info /teleop_turtle       > evidence/pr01/teleop-info.txt
ros2 topic type /turtle1/pose       > evidence/pr01/pose-type.txt
ros2 topic echo /turtle1/pose --once > evidence/pr01/pose-before.txt
```

Замер частоты `/turtle1/pose` в покое:

```bash
TIMEFORMAT='elapsed_seconds=%R'
{ time timeout --signal=INT 15s ros2 topic hz /turtle1/pose \
  > evidence/pr01/pose-hz.txt 2>&1; } 2> evidence/pr01/pose-hz-duration.txt
printf 'exit=%s\n' "$?" > evidence/pr01/pose-hz-exit.txt
```

Полный сценарий разрыва (домен 17) и восстановления — в `evidence/pr01/graph.md`.

## PR02 — порядок сборки и запуска

### Сборка

```bash
source /opt/ros/jazzy/setup.bash
cd "$(git rev-parse --show-toplevel)"
set -o pipefail
colcon build --symlink-install --packages-select turtle_bringup \
  2>&1 | tee evidence/pr02/build.txt
source install/setup.bash
ros2 pkg prefix turtle_bringup     # → путь внутри install/
```

### Запуск launch-файла

Терминал A:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=16
ros2 launch turtle_bringup sim.launch.py
```

Проверка графа (терминал C):

```bash
ros2 node list --no-daemon --spin-time 2
# → /turtlesim
```

Остановка — `Ctrl+C` в A.

### Доставка команды (терминал B)

```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

Проверка в C:

```bash
ros2 topic echo /turtle1/pose --once
```

### Ошибочный топик (для PR02, стадия «сломать»)

```bash
ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'

ros2 topic info /cmd_vel --verbose
# → Publisher count: 1, Subscription count: 0
```

Полное сравнение «до / сбой / после» — в `evidence/pr02/commands.md`,
типы сообщений — в `evidence/pr02/types.md`.

## Артефакты

| Путь | Содержимое |
|---|---|
| `src/turtle_bringup/` | пакет: `package.xml`, `setup.py`, `launch/sim.launch.py` |
| `evidence/pr01/` | улики PR01 (`report.json`, `graph.md`, `*.txt`) |
| `evidence/pr02/` | улики PR02 (`report.json`, `commands.md`, `types.md`, `build*.txt`) |
| `AI_USAGE.md` | записи об использовании ИИ по каждой ПР |
| `.github/workflows/` | CI: сборка `turtle_bringup`, запуск `check_practice.py` |

## PR03 — нода `patrol`: своя нода с подпиской, таймером и публикацией

Пакет `patrol` создаёт ноду, которая следит за `/turtle1/pose` и раз в 0.1 с
отправляет `Twist` в `cmd_vel` (относительное имя). В `cmd_vel` — `linear.x=0.5`,
`angular.z=0.3`, что даёт круг радиусом ≈1.67.

### Сборка и тесты

```bash
source /opt/ros/jazzy/setup.bash
cd "$(git rev-parse --show-toplevel)"
colcon build --symlink-install --packages-select patrol
colcon test  --packages-select patrol --event-handlers console_direct+
colcon test-result --verbose
```

### Запуск

Терминал A — симулятор:

```bash
source install/setup.bash
ros2 run turtlesim turtlesim_node
```

Терминал B — нода патруля (с ремапом топика):

```bash
source install/setup.bash
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

Терминал C — измерение частоты публикации:

```bash
timeout 10s ros2 topic hz /turtle1/cmd_vel
```

Ожидаемо: ≈10 Гц.

### Разбор имени топика

Без ремапа нода публикует в `/cmd_vel` (относительное имя + неймспейс `/`),
а turtlesim слушает `/turtle1/cmd_vel`. Доставки нет. Проверка:

```bash
ros2 topic info /cmd_vel --verbose
# Publisher count: 1, Subscription count: 0
```

Ремап `-r cmd_vel:=/turtle1/cmd_vel` связывает publisher с подписчиком.

## PR04 — параметры ноды `patrol`

Нода `patrol` получила три параметра, которыми можно менять поведение
на ходу, без перезапуска:

| Параметр | По умолчанию | Диапазон |
|---|---|---|
| `linear_speed` | 0.5 м/с | 0.0–1.0 |
| `turn_rate` | 0.3 рад/с | −1.0–1.0 |
| `publish_hz` | 10.0 Гц | 1.0–30.0 |

Недопустимые значения (вне диапазона, NaN, ±inf) отклоняются с
сохранением текущего состояния.

### Сборка и тесты

```bash
source /opt/ros/jazzy/setup.bash
cd "$(git rev-parse --show-toplevel)"
colcon build --symlink-install --packages-select patrol
colcon test  --packages-select patrol --event-handlers console_direct+
colcon test-result --verbose
```

### Запуск

Терминал A:

```bash
source install/setup.bash
ros2 run turtlesim turtlesim_node
```

Терминал B:

```bash
source install/setup.bash
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

### Изменение параметров на ходу

```bash
ros2 param list /patrol
ros2 param get  /patrol publish_hz
ros2 param set  /patrol publish_hz 5.0     # частота упадёт до 5 Гц

ros2 param set  /patrol publish_hz 0.0     # отклонено: значение вне диапазона
ros2 param get  /patrol publish_hz         # всё ещё 5.0

ros2 param set  /patrol linear_speed 0.8   # скорость вырастет
```

При смене `publish_hz` старый таймер останавливается и уничтожается,
затем создаётся новый с периодом `1/publish_hz`. Двух одновременно
работающих таймеров не остаётся.

## PR05 — launch с аргументами, namespace и записью MCAP

Одна launch-команда поднимает систему в пространстве имён `/robot_a`,
ретранслирует `/turtle1/pose` в `/robot_a/sensor_pose` с QoS
best_effort и (опционально) пишет поток в MCAP. Демонстрируется
несовместимость QoS: reliable-подписчик не получает best_effort-поток.

### Состав

| Компонент | Роль |
|---|---|
| `course_bringup` | пакет с launch-файлами |
| `pose_relay` | нода: `/turtle1/pose` → `sensor_pose` (best_effort) |
| `patrol.launch.py` | запускает `pose_relay` + опциональный `ros2 bag record` |
| `config/qos-overrides.yaml` | профиль QoS для replay |

### Сборка

```bash
source /opt/ros/jazzy/setup.bash
cd "$(git rev-parse --show-toplevel)"
colcon build --symlink-install --packages-select course_bringup
colcon test  --packages-select course_bringup --event-handlers console_direct+
colcon test-result --verbose
```

### Запуск

Терминал A — turtlesim глобально:

```bash
source install/setup.bash
ros2 run turtlesim turtlesim_node
```

Терминал B — launch (без записи):

```bash
source install/setup.bash
ros2 launch course_bringup patrol.launch.py \
  namespace:=robot_a subscriber_reliability:=best_effort record:=false
```

Терминал C — проверка доставки:

```bash
ros2 topic echo /robot_a/sensor_pose \
  --qos-reliability best_effort --once
```

Ожидаемый результат: сообщение приходит.

### Демонстрация QoS-разрыва

Терминал B — перезапуск с reliable-подписчиком:

```bash
ros2 launch course_bringup patrol.launch.py \
  namespace:=robot_a subscriber_reliability:=reliable record:=false
```

Терминал C — проверка:

```bash
ros2 topic list | grep sensor_pose
# /robot_a/sensor_pose    ← топик виден

ros2 topic info /robot_a/sensor_pose --verbose
# Publisher count: 1     QoS: BEST_EFFORT
# Subscription count: 1  QoS: RELIABLE    ← несовместимо

timeout 3s ros2 topic echo /robot_a/sensor_pose \
  --qos-reliability reliable --once
# завершается по timeout, сообщений нет
```

### Запись в MCAP

Терминал B:

```bash
ros2 launch course_bringup patrol.launch.py \
  namespace:=robot_a subscriber_reliability:=best_effort record:=true
```

Через 10–20 секунд — `Ctrl+C`. Запись окажется в `evidence/pr05/bag/`.

Проверка:

```bash
ros2 bag info evidence/pr05/bag
# Topic: /robot_a/sensor_pose | Type: turtlesim/msg/Pose | Count: N
```

### Replay с QoS-override

Терминал B:

```bash
ros2 bag play evidence/pr05/bag \
  --qos-profile-overrides-path config/qos-overrides.yaml
```

Терминал C:

```bash
timeout 3s ros2 topic echo /robot_a/sensor_pose \
  --qos-reliability best_effort --once
```

Сообщение приходит — значит, тот же QoS, что на живом потоке, работает и на записи.

### Ключевой момент

`add_on_set_parameters_callback` из PR04 в этой работе не используется; здесь
важно, что **QoS publisher’а и subscriber’а должны совпадать по reliability**.
best_effort publisher не может обслужить reliable subscriber — discovery
видит оба endpoint’а, но DDS не связывает их. Это отличается от PR02/PR03,
где конфликт был в имени топика: здесь имя и тип совпадают, а поток всё
равно не идёт.
