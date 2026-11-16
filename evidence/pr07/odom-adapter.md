# PR07 — Адаптер одометрии

## Исходные и нормализованные фреймы
Исходное сообщение из Gazebo (`/vehicle/odom_gz`) имеет фреймы:
*   `header.frame_id`: `course_ackermann/odom`
*   `child_frame_id`: `course_ackermann/base_link`

Наш адаптер (`odom_adapter.py`) переименовывает их в общеупотребимые:
*   `header.frame_id`: `odom`
*   `child_frame_id`: `base_link`

Адаптер сохраняет `stamp`, `pose`, `twist` и обе матрицы `covariance`.

## Владельцы TF
*   Статические связи (камера, лидар, IMU) публикует `robot_state_publisher` из ПР06.
*   Динамическую связь `odom` → `base_link` публикует **только** наш `odom_adapter`. Других издателей этого TF нет, чтобы избежать конфликтов.

## Тест сохранения метки времени
Метка времени (`header.stamp`) берется из исходного сообщения Gazebo (время симуляции) и переносится без изменений. Проверка в записи bag показала, что сообщения `/vehicle/odom` идут с корректными метками симуляции.

