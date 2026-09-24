# PR02 — топики и типы сообщений

Дистрибутив ROS 2: **jazzy**.
Тип позы turtlesim в jazzy: `turtlesim/msg/Pose`.
(В lyrical тот же интерфейс называется `turtlesim_msgs/msg/Pose`.)

## 1. Основные топики опыта

| Топик | Тип | Назначение | Кто публикует / подписан |
|---|---|---|---|
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | команды движения черепахе | публикует CLI/teleop, подписан `turtlesim_node` |
| `/turtle1/pose` | `turtlesim/msg/Pose` | текущее состояние черепахи | публикует `turtlesim_node`, подписан CLI/наблюдатель |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | топик из ошибочного опыта | публикует CLI, подписчиков нет |

Тип `/turtle1/pose` получен командой:

```
ros2 topic type /turtle1/pose
# → turtlesim/msg/Pose
```

## 2. `geometry_msgs/msg/Twist`

Структура (сокращённо):

```
Vector3  linear
Vector3  angular
```

Каждое поле `Vector3` — это `float64 x, y, z`.

| Поле | Смысл | Значение в опыте |
|---|---|---|
| `linear.x` | линейная скорость вдоль текущего курса, м/с | `1.0` |
| `linear.y` | поперечная скорость, м/с; в turtlesim не используется | `0.0` |
| `linear.z` | вертикальная, м/с; в 2D не используется | `0.0` |
| `angular.x` | вращение вокруг оси X; в 2D не используется | `0.0` |
| `angular.y` | вращение вокруг оси Y; в 2D не используется | `0.0` |
| `angular.z` | угловая скорость вокруг вертикальной оси, рад/с | `0.5` |

В опыте отправлялось:

```
{linear: {x: 1.0}, angular: {z: 0.5}}
```

— черепаха едет вперёд со скоростью 1.0 и одновременно поворачивает против
часовой стрелки со скоростью 0.5 рад/с (при виде сверху, как в окне turtlesim).

## 3. `turtlesim/msg/Pose`

Структура (полная):

```
float32 x
float32 y
float32 theta
float32 linear_velocity
float32 angular_velocity
```

| Поле | Смысл |
|---|---|
| `x` | координата по горизонтали в поле симулятора |
| `y` | координата по вертикали |
| `theta` | курс в радианах; `0` — вправо, отсчёт против часовой стрелки |
| `linear_velocity` | модуль текущей линейной скорости, м/с |
| `angular_velocity` | текущая угловая скорость, рад/с |

Публикуется turtlesim с частотой около 62.5 Гц (наблюдалось в PR01, для
этой же сборки turtlesim частота та же — см. `evidence/pr01/pose-hz.txt`).

## 4. Почему правильного типа сообщения недостаточно

`geometry_msgs/msg/Twist` в `/cmd_vel` и в `/turtle1/cmd_vel` — один и тот же
тип. DDS-граф сопоставляет publisher и subscriber по **паре** «имя топика +
тип сообщения». Если имя не совпадает, доставки нет, даже когда тип совпал:

```
ros2 topic info /cmd_vel --verbose
# Publisher count: 1, Subscription count: 0

ros2 topic info /turtle1/cmd_vel --verbose
# Publisher count: 0, Subscription count: 1
```

turtlesim подписан на `/turtle1/cmd_vel` и не знает про `/cmd_vel`. Издатель
обнаруживается в графе (виден в `ros2 topic list`), но конечного получателя
у него нет.

Отсюда различие, которое требуется объяснить:

- **обнаружение** — узел или топик видны в графе; это результат работы
  discovery DDS по имени/типу;
- **доставка** — сообщение реально доходит, только если у publisher и subscriber
  совпали и имя, и тип.
