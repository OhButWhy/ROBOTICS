# PR08 — Диагностика TF

## До исправления (Дефект)
Запуск локализации с `params_file:=amcl-defect.yaml` (где `base_frame_id: chassis`).
В логах AMCL сразу появляется циклическая ошибка:
`[ERROR] [amcl]: Couldn't transform from lidar_link to chassis, even though the message notifier is in use: ("chassis" passed to lookupTransform argument target_frame does not exist. )`

Это приводит к тому, что AMCL не обновляет позу (застревает в 0,0,0), а трансформация `map -> odom` начинает "убегать" от одометрии, чтобы скомпенсировать движение робота. Локализация не работает.

## После исправления
Запуск с `params_file:=amcl.yaml` (`base_frame_id: base_link`).
Ошибка исчезает. Доступность `map->odom` составляет 100% (200/200 запросов), медиана ковариации = 0.117. Робот успешно локализуется.
