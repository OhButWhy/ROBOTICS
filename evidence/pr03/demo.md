# PR03 — демонстрация и разбор механизмов

## 1. Что делает нода

Пакет `patrol` содержит ноду `/patrol`:

- подписка на `/turtle1/pose` (поле `self._sub`),
- callback `_on_pose` только сохраняет последнее сообщение в `self._pose`,
- таймер `0.1` с вызывает `_on_timer`,
- publisher `Twist` на относительном `cmd_vel` (поле `self._pub`),
- логика команды — в чистой функции `command_from_pose(pose)`.

## 2. Роли `init`, `spin`, callback, Ctrl+C

**`rclpy.init(args=args)`** — инициализация клиентской библиотеки ROS 2
в текущем процессе: DDS-участник, сигнальные обработчики, runtime.
Вызывается один раз до создания нод.

**`rclpy.spin(node)`** — блокирующий цикл executor’а: слушает DDS и
таймеры, вызывает зарегистрированные callbacks. Без него нода
зарегистрирована в графе, но логика не выполняется.

**Callbacks**:

- `_on_pose` — вызывается при получении сообщения `Pose`. Только
  сохраняет `self._pose`, никакой логики.
- `_on_timer` — вызывается раз в 0.1 с. Формирует `Twist` через
  `command_from_pose` и публикует.

Оба должны быть быстрыми: однопоточный executor блокируется, пока
callback работает.

**Ctrl+C** — посылает `SIGINT`, `rclpy` превращает его в
`KeyboardInterrupt` внутри `spin`. Обработчик:

```python
try:
    rclpy.spin(node)
except KeyboardInterrupt:
    pass
finally:
    node.destroy_node()
    rclpy.shutdown()
```

`destroy_node` дерегистрирует publisher/subscriber/timer из DDS,
`shutdown` финализирует библиотеку. **Команда торможения не отправляется.**

## 3. Что происходит с turtlesim после остановки

turtlesim продолжает ехать с последней полученной скоростью, затем
сам гасит её (внутренний декей). Между Ctrl+C и остановкой черепахи
есть заметная задержка. Это не «мгновенная команда стоп» — нода
просто перестала публиковать.

## 4. Разрыв и исправление

### Сломанное состояние — без ремапа

```
ros2 run patrol patrol

ros2 topic info /cmd_vel --verbose
# Publisher count: 1
#   Node name: patrol
#   Topic type: geometry_msgs/msg/Twist
# Subscription count: 0

ros2 topic info /turtle1/cmd_vel --verbose
# Publisher count: 0
# Subscription count: 1
#   Node name: turtlesim
```

Черепаха стоит.

### Исправлено — ремап

```
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel

ros2 topic info /turtle1/cmd_vel --verbose
# Publisher count: 1
#   Node name: patrol
# Subscription count: 1
#   Node name: turtlesim
```

Черепаха движется по кругу радиусом R = linear.x / angular.z = 0.5 / 0.3 ≈ 1.67.

### Измерение частоты

```
timeout 10s ros2 topic hz /turtle1/cmd_vel

average rate: 10.004
        min: 0.099s max: 0.101s std dev: 0.00048s window: 12
average rate: 10.001
        min: 0.099s max: 0.101s std dev: 0.00056s window: 22
...
```

Значения совпадают с настройкой таймера (0.1 с → 10 Гц).
Единичная просадка до ~9.26 в одном окне — сетевой/scheduling
hiccup, не влияет на оценку средней частоты.

## 5. Почему относительное имя вообще нужно

Абсолютное имя `/turtle1/cmd_vel` жёстко привязывает ноду к
конкретной черепахе. Относительное `cmd_vel` + ремап позволяют:

- переиспользовать ноду в другом контексте (запустить в другом
  неймспейсе, перенаправить команду другой черепахе);
- писать код независимо от топологии запуска;
- менять топологию без правки исходников.
