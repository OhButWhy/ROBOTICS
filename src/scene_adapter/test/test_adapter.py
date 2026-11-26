import os

import pytest
import rclpy
import rclpy.parameter
from scene_adapter.node import SceneAdapter


@pytest.fixture
def adapter():
    # Создаём ноду, но не запускаем spin
    rclpy.init()
    node = SceneAdapter()
    yield node
    node.destroy_node()
    rclpy.shutdown()


def load_fixture(name):
    path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'fixtures',
        'vlm',
        name)
    with open(path, 'r') as f:
        return f.read()


def test_clear_valid(adapter):
    raw = load_fixture('scene-clear.json')
    data, reason = adapter.validate_and_parse(raw, now_s=0.1)
    assert data is not None
    assert reason is None
    msg = adapter.json_to_ros(data)
    assert msg.status == 0  # STATUS_VALID


def test_low_confidence(adapter):
    raw = load_fixture('scene-low-confidence.json')
    data, reason = adapter.validate_and_parse(raw, now_s=0.1)
    assert data is None
    assert reason == 'low_confidence'


def test_stale(adapter):
    raw = load_fixture('scene-stale.json')
    # now_s=2.0, stamp_s=0 (или 1) -> > max_age_s (0.25)
    data, reason = adapter.validate_and_parse(raw, now_s=2.0)
    assert data is None
    assert reason == 'stale_input'


def test_extra_command_rejected(adapter):
    raw = load_fixture('scene-extra-command.json')
    data, reason = adapter.validate_and_parse(raw, now_s=0.1)
    assert data is None
    assert reason == 'invalid_schema'


def test_cache_key_components(adapter):
    img = b'img1'
    prompt = 'prompt1'
    config = {'temperature': 0.7}

    k1 = adapter.compute_cache_key(img, prompt, 'model', config)

    # Меняем картинку
    k2 = adapter.compute_cache_key(b'img2', prompt, 'model', config)
    assert k1 != k2

    # Меняем промпт
    k3 = adapter.compute_cache_key(img, 'prompt2', 'model', config)
    assert k1 != k3

    # Меняем модель
    k4 = adapter.compute_cache_key(img, prompt, 'model2', config)
    assert k1 != k4

    # Меняем конфиг
    k5 = adapter.compute_cache_key(img, prompt, 'model', {'temperature': 0.8})
    assert k1 != k5

# Тест на кэш (miss -> backend, hit -> no backend)


def test_cache_hit_miss(adapter, tmp_path):
    adapter.set_parameters([
        rclpy.parameter.Parameter(
            'cache_dir', rclpy.Parameter.Type.STRING, str(tmp_path)),
        rclpy.parameter.Parameter(
            'mode', rclpy.Parameter.Type.STRING, 'cache'),
    ])

    calls = {'count': 0}

    def mock_backend(img, prompt, config):
        calls['count'] += 1
        return load_fixture('scene-clear.json')

    adapter.backend = mock_backend

    # 1. Первый вызов -> miss, backend вызывается
    adapter.process_frame(b'img', 'prompt')
    assert calls['count'] == 1

    # 2. Второй вызов с теми же данными -> hit, backend НЕ вызывается
    adapter.process_frame(b'img', 'prompt')
    assert calls['count'] == 1
