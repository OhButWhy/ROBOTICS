# PR01 - Граф ROS 2: исправное состояние, разрыв и восстановление

Демонстрация базового графа ROS 2 (turtlesim + teleop) и эффекта
рассогласования `ROS_DOMAIN_ID` между участниками.

## Среда

- ROS 2: **jazzy** (`osrf/ros:jazzy-desktop-full`)
- Запуск: WSL2 (Ubuntu 24.04)
- Один рабочий каталог `~/robotics_ws`, образ/дистрибутив фиксированы.

## Порядок запуска

Три терминала A/B/C. В каждом перед началом:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=16
cd ~/robotics_ws
```

### Терминал A - симулятор

```bash
ros2 run turtlesim turtlesim_node
```

### Терминал B - управление

```bash
ros2 run turtlesim turtle_teleop_key
# фокус оставить в этом терминале, стрелками управлять черепахой
```

### Терминал C - сбор информации

```bash
mkdir -p evidence/pr01
ros2 doctor --report                > evidence/pr01/doctor.txt 2>&1
ros2 node list --no-daemon --spin-time 2 > evidence/pr01/nodes-before.txt
ros2 topic list -t                  > evidence/pr01/topics.txt
ros2 node info /turtlesim           > evidence/pr01/turtlesim-info.txt
ros2 node info /teleop_turtle       > evidence/pr01/teleop-info.txt
ros2 topic type /turtle1/pose       > evidence/pr01/pose-type.txt
POSE_TYPE=$(cat evidence/pr01/pose-type.txt)
ros2 topic echo /turtle1/pose --once > evidence/pr01/pose-before.txt
```

Замер частоты `/turtle1/pose` в покое (15 с, завершение по `SIGINT`):

```bash
TIMEFORMAT='elapsed_seconds=%R'
{ time timeout --signal=INT 15s ros2 topic hz /turtle1/pose \
  > evidence/pr01/pose-hz.txt 2>&1; } 2> evidence/pr01/pose-hz-duration.txt
printf 'exit=%s\n' "$?" > evidence/pr01/pose-hz-exit.txt
```

После одного нажатия ↑ в B и остановки черепахи:

```bash
ros2 topic echo /turtle1/pose --once > evidence/pr01/pose-after-key-working.txt
```

## Воспроизведение дефекта (разрыв графа)

В B останавливаем teleop (`Ctrl+C`) и перезапускаем в другом домене:

```bash
export ROS_DOMAIN_ID=17
ros2 run turtlesim turtle_teleop_key
```

В C - проверка в домене 17:

```bash
export ROS_DOMAIN_ID=17
ros2 node list --no-daemon --spin-time 2 > evidence/pr01/nodes-broken.txt
timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once \
  > evidence/pr01/pose-broken.txt 2>&1
printf 'exit=%s\n' "$?" > evidence/pr01/pose-broken-exit.txt
```

Нажимаем ↑ в B. Контрольное чтение из домена симулятора:

```bash
ROS_DOMAIN_ID=16 ros2 topic echo /turtle1/pose --once \
  > evidence/pr01/pose-after-key-broken-control.txt
```

Ожидаемый симптом: `nodes-broken.txt` содержит только `/teleop_turtle`,
`pose-broken-exit.txt` = 124 (таймаут), черепаха не двигается.

## Восстановление

В B возвращаем домен и перезапустить teleop:

```bash
export ROS_DOMAIN_ID=16
ros2 run turtlesim turtle_teleop_key
```

В C - та же проверка, что и в исправном состоянии:

```bash
export ROS_DOMAIN_ID=16
ros2 node list --no-daemon --spin-time 2 > evidence/pr01/nodes-fixed.txt
timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once \
  > evidence/pr01/pose-fixed.txt 2>&1
printf 'exit=%s\n' "$?" > evidence/pr01/pose-fixed-exit.txt

# после ↑ в B:
ros2 topic echo /turtle1/pose --once > evidence/pr01/pose-after-key-fixed.txt
```

Ожидаемый результат: `nodes-fixed.txt` = 2 строки, `pose-fixed-exit.txt` = 0,
поза меняется после ↑.

## Артефакты

| Путь | Содержимое |
|---|---|
| `evidence/pr01/doctor.txt` | `ros2 doctor --report` |
| `evidence/pr01/topics.txt` | список топиков с типами |
| `evidence/pr01/pose-hz.txt` | `ros2 topic hz` за 15 с |
| `evidence/pr01/nodes-{before,broken,fixed}.txt` | три состояния графа |
| `evidence/pr01/pose-*.txt` | позы в ключевых точках |
| `evidence/pr01/environment.json` | описание среды |
| `evidence/pr01/graph.md` | разбор трёх состояний и причины сбоя |
| `report.json` | формальный отчёт PR01 |
