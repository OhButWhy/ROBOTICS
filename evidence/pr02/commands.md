# PR02 — команды и сравнение «до / сбой / после»

## 1. Три Linux-команды, использованные в работе

### 1.1 `mkdir -p src evidence/pr02`

- **Назначение:** создать каталоги `src/` и `evidence/pr02/`, включая вложенные;
  `-p` подавляет ошибку, если каталог уже существует, и создаёт промежуточные
  уровни за один вызов.
- **Результат у меня:** обе папки появились в корне репозитория;
  `ls -a` показал `src` и `evidence` рядом с `.git/`, `README.md`.

### 1.2 `source install/setup.bash`

- **Назначение:** выполнить содержимое скрипта **в текущем** shell, чтобы в него
  попали переменные окружения (`AMENT_PREFIX_PATH`, `PYTHONPATH`, `PATH`) для
  только что собранного workspace.
- **Результат у меня:** после `source install/setup.bash` команда
  `ros2 pkg prefix turtle_bringup` вернула путь внутри `install/`, а не
  `/opt/ros/jazzy`.

### 1.3 `grep` / `cat` для чтения лога

- **Назначение:** `cat` печатает файл целиком; `grep` ищет в нём строку,
  когда лог длинный.
- **Результат у меня:** `grep -i 'error' evidence/pr02/build.txt` после
  успешной сборки ничего не вывел — значит, ошибок не было.

## 2. Чем `>` отличается от `|`

- `>` **перенаправляет поток в файл**: `colcon build … > log.txt` пишет stdout
  в файл, **перезаписывая** его. В терминале вывода не видно. С `2>&1` туда же
  уходит stderr.
- `|` **соединяет stdout одной программы со stdin другой**: `colcon build … | tee log.txt`
  отдаёт вывод команде `tee`, которая **одновременно** печатает его на экран и
  пишет в файл. Ничего не перезаписывается «молча».

В этой работе `| tee` использовался, чтобы видеть ход сборки и одновременно
получить `evidence/pr02/build.txt`.

## 3. Чем `source` отличается от запуска новой программы

- `source file` выполняет команды файла **в текущем** процессе shell. Переменные,
  объявленные внутри, остаются в текущем терминале.
- `./file` (или любой запуск команды) порождает **дочерний** процесс. Его
  переменные окружения умирают вместе с ним, в родительском терминале их не видно.

Поэтому `bash setup.bash` **не** заменит `source setup.bash` — первый вариант
подключит окружение только для дочернего процесса.

## 4. Запуск launch и проверка графа

Сборка пустого пакета (evidence/pr02/build-empty.txt):

Starting >>> turtle_bringup
Finished <<< turtle_bringup [2.16s]
Summary: 1 package finished [2.34s]

Сборка с launch-файлом (evidence/pr02/build.txt):

Starting >>> turtle_bringup
Finished <<< turtle_bringup [1.58s]
Summary: 1 package finished [1.76s]

Обе сборки — без ошибок и предупреждений, `colcon` завершился с кодом 0
(в командах стоял `set -o pipefail`, так что ненулевой статус был бы виден).

ros2 launch turtle_bringup sim.launch.py
ros2 node list --no-daemon --spin-time 2
# → /turtlesim

## 5. Доставка команды: до / сбой / после

### До — правильное имя топика

```
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
ros2 topic echo /turtle1/pose --once
```

Поза до: x≈…, y≈…, theta≈…
Поза после: x≈…, y≈…, theta≈… — черепаха сдвинулась, поворот совпал с `angular.z=0.5`.

### Сбой — неверное имя `/cmd_vel`

```
ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'

ros2 topic info /cmd_vel --verbose
# → Publisher count: 1, Subscription count: 0
ros2 topic info /turtle1/cmd_vel --verbose
# → Publisher count: 0, Subscription count: 1
```

Черепаха **не двигалась**, хотя тип `geometry_msgs/msg/Twist` абсолютно
правильный. Издатель виден в графе, но у него нет подписчиков.

### После — снова `/turtle1/cmd_vel`

```
ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'

ros2 topic info /turtle1/cmd_vel --verbose
# → Publisher count: 1, Subscription count: 1
```

Черепаха движется, после `Ctrl+C` — останавливается.

## 6. Почему правильного типа сообщения недостаточно

DDS сопоставляет publisher и subscriber по **паре** «имя топика + тип сообщения».
Правильный тип сам по себе не создаёт связь, если имя не совпадает. В графе
`/cmd_vel` и `/turtle1/cmd_vel` — два разных топика с одним и тем же типом;
`turtlesim` подписан только на второй. Издатель в `/cmd_vel` остаётся без
получателя, и сообщение уходит в пустоту.

Это и есть различие:
- **обнаружение** — узел/топик видны в графе (`ros2 topic list`, `topic info`);
- **доставка** — сообщение реально доходит, только если у обеих сторон совпали
  имя и тип.
