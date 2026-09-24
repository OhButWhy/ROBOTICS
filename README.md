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
