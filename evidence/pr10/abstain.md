# PR10 — Abstain (отбраковка) и кэширование

## Пороги
- **abstain_threshold = 0.5**: Если VLM не уверен хотя бы наполовину (confidence < 0.5), мы не доверяем ответу.
- **max_age_s = 0.25**: Если ответ VLM старше 0.25 секунды, он считается устаревшим (робот мог уехать).

## Причины unknown для фикстур
| Fixture | now_s | Причина |
|---|---:|---|
| scene-clear.json | 0.1 | valid (проходит) |
| scene-low-confidence.json | 0.1 | low_confidence (confidence=0.24 < 0.5) |
| scene-stale.json | 2.0 | stale_input (2.0 - 1.0 = 1.0 > 0.25) |
| scene-extra-command.json | 0.1 | invalid_schema (лишнее поле drive) |

## Дефект кэша (Стадия 2)
Мы намеренно удалили `prompt_sha256` из ключа кэша. В результате:
- При первом запросе с `image1 + prompt1` кэш сохраняет ответ.
- При втором запросе с `image1 + prompt2` (изменен промпт, но картинка та же) ключ совпадает, и кэш возвращает **старый** ответ от `prompt1`.
- Это доказывает, что промпт должен быть частью ключа, иначе адаптер будет использовать неверные сцены.

## Кэш-ключ (после исправления)
Ключ = SHA-256 от canonical JSON с полями:
- `image_sha256`
- `prompt_sha256`
- `model_id`
- `generation_config`
- `schema_version: 1`

Изменение любого из 5 компонентов дает cache miss. Это доказано тестом `test_cache_key_components`.
