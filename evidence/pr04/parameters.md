# PR04 — динамические параметры ноды `patrol`

## 1. Объявленные параметры

| Имя | По умолчанию | Допустимый диапазон |
|---|---|---|
| `linear_speed` | 0.5 м/с | 0.0 ≤ v ≤ 1.0 |
| `turn_rate` | 0.3 рад/с | −1.0 ≤ ω ≤ 1.0 |
| `publish_hz` | 10.0 Гц | 1.0 ≤ f ≤ 30.0 |

Все значения — конечные числа. `NaN`, `+inf`, `-inf` и значения вне
диапазона отклоняются без изменения активного состояния ноды.

Объявление — в `Patrol.__init__`:

```python
self.declare_parameter('linear_speed', 0.5)
self.declare_parameter('turn_rate', 0.3)
self.declare_parameter('publish_hz', 10.0)
self.add_on_set_parameters_callback(self._on_param_change)
```

## 2. Валидация до применения

Callback `_on_param_change` получает список изменений и **до** того, как
они применятся, проверяет каждое:

```python
def _on_param_change(self, params):
    for p in params:
        if not validate_param(p.name, p.value):
            return SetParametersResult(
                successful=False,
                reason=f'{p.name}={p.value} недопустимо',
            )
    for p in params:
        if p.name == 'publish_hz':
            self._restart_timer(p.value)
    return SetParametersResult(successful=True)
```

Ключевые моменты:

- Если хотя бы один параметр из пачки невалиден — **вся** пачка отклоняется,
  состояние остаётся неизменным.
- `publish_hz` требует пересоздания таймера, поэтому применяется через
  `_restart_timer`. Параметры `linear_speed` и `turn_rate` читаются в
  `_on_timer` в момент публикации — им достаточно просто обновиться в
  параметрах, никаких действий не нужно.

## 3. Пересоздание таймера

```python
def _restart_timer(self, hz):
    if self._timer is not None:
        self._timer.cancel()
        self.destroy_timer(self._timer)
    self._timer = self.create_timer(1.0 / hz, self._on_timer)
```

Прежний таймер обязательно останавливается (`cancel`) и удаляется
(`destroy_timer`) **до** создания нового. Иначе два таймера будут
публиковать одновременно, и реальная частота станет суммой.

## 4. Нормальное изменение частоты: 10 → 5 Гц

Терминал C, нода работает с ремапом `-r cmd_vel:=/turtle1/cmd_vel`.

```
$ ros2 param get /patrol publish_hz
Double value is: 10.0

$ ros2 param set /patrol publish_hz 5.0
Set parameter successful

$ ros2 param get /patrol publish_hz
Double value is: 5.0

$ timeout 5s ros2 topic hz /turtle1/cmd_vel
average rate: 4.999
        min: 0.199s max: 0.201s std dev: 0.00058s window: 5
```

Частота публикации в `/turtle1/cmd_vel` действительно упала до ≈5 Гц —
таймер пересоздан с периодом `1/5.0 = 0.2 s`. Черепаха продолжает
ехать по кругу, команды просто приходят реже.

## 5. Отклонение недопустимого значения

При включённой валидации попытка выставить `publish_hz = 0.0`:

```
$ ros2 param get /patrol publish_hz
Double value is: 10.0

$ ros2 param set /patrol publish_hz 0.0
Setting parameter failed: publish_hz=0.0 недопустимо

$ ros2 param get /patrol publish_hz
Double value is: 10.0

$ timeout 3s ros2 topic hz /turtle1/cmd_vel
average rate: 10.004
        min: 0.099s max: 0.101s std dev: 0.00048s window: 12
```

Три факта доказаны:

1. **Ноль отклонён** — команда `param set` вернула ошибку.
2. **Прежнее значение сохранено** — `param get` показывает 10.0.
3. **Поток не изменился** — `topic hz` по-прежнему ≈10 Гц.

Никакого разрушения активного состояния не произошло.

## 6. Воспроизведение отказа при отключённой валидации

Для проверки стадии «сломать» проверка частоты была временно
закомментирована в `_on_param_change` (отдельная ветка/коммит, в
основную историю не входит). При том же вызове:

```
$ ros2 param set /patrol publish_hz 0.0
Set parameter successful            ← валидация отсутствует, значение прошло

$ ros2 param get /patrol publish_hz
Double value is: 0.0

$ timeout 3s ros2 topic hz /turtle1/cmd_vel
(нет данных)

$ ros2 node list
/patrol не найден
```

Причина: `_restart_timer` выполняет `1.0 / 0` — `ZeroDivisionError`,
нода завершается, публикация прекращается. Это **воспроизводимый
отказ**: одно и то же значение даёт одну и ту же ошибку.

Полный лог — в `evidence/pr04/param-set-broken.txt`.

После возврата проверки (`if not validate_param(...)`) тот же вызов
`publish_hz = 0.0` снова отклоняется, нода продолжает работать —
это уже показано в разделе 5.

## 7. Роли параметров и таймера

| Параметр | Что меняет | Требует пересоздания таймера |
|---|---|---|
| `linear_speed` | `cmd.linear.x` в `_on_timer` | нет |
| `turn_rate` | `cmd.angular.z` в `_on_timer` | нет |
| `publish_hz` | период таймера | **да** |

`linear_speed` и `turn_rate` читаются из параметров **при каждой
публикации**, поэтому их изменение вступает в силу на следующем тике
(≤0.1 с при `publish_hz=10`). `publish_hz` меняет сам таймер — поэтому
идёт через `_restart_timer`.

## 8. Служебные интерфейсы turtlesim

### `/clear` — сервис

```
$ ros2 service list | grep clear
/clear

$ ros2 service call /clear std_srvs/srv/Empty
requester: making request: std_srvs.srv.Empty_Request()

response:
std_srvs.srv.Empty_Response()
```

Экран очищается, черепаха остаётся на месте и с тем же курсом.

### `/turtle1/rotate_absolute` — действие

```
$ ros2 action list -t
/turtle1/rotate_absolute [turtlesim/action/RotateAbsolute]

$ ros2 action info /turtle1/rotate_absolute
Action: /turtle1/rotate_absolute
Action clients: 0
Action servers: 1
    /turtlesim
```

### Отличие запроса от цели

**Запрос (service)** — синхронный: клиент отправляет данные, сервер
выполняет **короткую** операцию и возвращает результат, всё это в одном
обмене. `/clear` пример: сервер стёр экран за миллисекунды, клиент
дождался ответа и продолжил.

**Цель (action)** — асинхронная и **длительная**: клиент отправляет goal,
сервер может выполнять её секунды, присылая промежуточный progress
(feedback), а клиент в любой момент может отменить операцию. Пример:
`/turtle1/rotate_absolute` — поворот черепахи занимает заметное время,
поэтому оформлен как action, а не service.
