import hashlib
import json
import os

from ament_index_python.packages import get_package_share_directory
from builtin_interfaces.msg import Time
import jsonschema
import rclpy
from rclpy.node import Node
from robotics_course_interfaces.msg import SceneDescription


class SceneAdapter(Node):
    def __init__(self):
        super().__init__('scene_adapter')

        # Параметры
        self.declare_parameter('mode', 'mock')
        self.declare_parameter('fixture_path', '')
        self.declare_parameter('cache_dir', '/tmp/scene_cache')
        self.declare_parameter('prompt_path', '')
        self.declare_parameter('model_id', 'qwen3.8')
        self.declare_parameter('generation_config', '{}')
        self.declare_parameter('abstain_threshold', 0.5)
        self.declare_parameter('max_age_s', 0.25)
        self.declare_parameter('now_s_override', -1.0)

        self.pub = self.create_publisher(
            SceneDescription, '/perception/scene', 10)

        # Внедряемый backend (для live/cache)
        self.backend = None
        self._load_schema()

        # Запуск логики (для тестов можно вызывать метод process_frame
        # напрямую)
        self.timer = self.create_timer(1.0, self.process_frame)

    def _load_schema(self):
        pkg_dir = get_package_share_directory('scene_adapter')
        schema_path = os.path.join(
            pkg_dir,
            'contracts',
            'scene-description-v1.schema.json')
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)

    def compute_cache_key(
            self,
            image_bytes,
            prompt_text,
            model_id,
            config_dict):
        payload = {
            'image_sha256': hashlib.sha256(image_bytes).hexdigest(),
            'prompt_sha256': hashlib.sha256(
                prompt_text.encode('utf-8')).hexdigest(),
            'model_id': model_id,
            'generation_config': config_dict,
            'schema_version': 1}
        # Сортируем ключи и убираем пробелы (canonical JSON)
        payload_str = json.dumps(
            payload,
            sort_keys=True,
            separators=(
                ',',
                ':'))
        return hashlib.sha256(payload_str.encode('utf-8')).hexdigest()

    def get_now_s(self):
        # Для тестов переопределяем это значение
        return self.get_clock().now().nanoseconds * 1e-9

    def validate_and_parse(self, raw_json_str, now_s):
        try:
            data = json.loads(raw_json_str)
        except json.JSONDecodeError:
            return None, 'invalid_schema'

        # 1. Проверка схемы (включает additionalProperties: false, типы, enums)
        try:
            jsonschema.validate(instance=data, schema=self.schema)
        except jsonschema.ValidationError:
            return None, 'invalid_schema'

        # 2. Проверка времени (stale_input)
        if (now_s - data['stamp_s']) > self.get_parameter('max_age_s').value:
            return None, 'stale_input'

        # 3. Проверка уверенности (low_confidence)
        if data['confidence'] < self.get_parameter('abstain_threshold').value:
            return None, 'low_confidence'

        return data, None

    def make_canonical_unknown(self, reason):
        msg = SceneDescription()
        msg.version = 1
        msg.header.frame_id = 'base_link'
        msg.status = SceneDescription.STATUS_UNKNOWN
        msg.status_reason = reason
        msg.traffic_light = SceneDescription.LIGHT_UNKNOWN
        msg.direction_sign = SceneDescription.SIGN_UNKNOWN
        msg.lane_offset_m = 0.0
        msg.has_stop_line = False
        msg.stop_line_distance_m = 0.0
        msg.has_turn = False
        msg.turn_distance_m = 0.0
        msg.has_obstacle = False
        msg.obstacle_distance_m = 0.0
        msg.confidence = 0.0
        msg.source = 'unknown'
        return msg

    def json_to_ros(self, data):
        msg = SceneDescription()
        msg.version = data['version']

        sec = int(data['stamp_s'])
        nanosec = int((data['stamp_s'] - sec) * 1e9)
        msg.header.stamp = Time(sec=sec, nanosec=nanosec)
        msg.header.frame_id = data['frame_id']

        msg.status = (SceneDescription.STATUS_VALID
                      if data['status'] == 'valid'
                      else SceneDescription.STATUS_UNKNOWN)
        msg.status_reason = data['status_reason']
        msg.lane_offset_m = float(data['lane_offset_m'])

        light_map = {
            'none': SceneDescription.LIGHT_NONE,
            'red': SceneDescription.LIGHT_RED,
            'yellow': SceneDescription.LIGHT_YELLOW,
            'green': SceneDescription.LIGHT_GREEN,
            'unknown': SceneDescription.LIGHT_UNKNOWN,
        }
        msg.traffic_light = light_map[data['traffic_light']]

        sign_map = {
            'none': SceneDescription.SIGN_NONE,
            'left': SceneDescription.SIGN_LEFT,
            'right': SceneDescription.SIGN_RIGHT,
            'straight': SceneDescription.SIGN_STRAIGHT,
            'unknown': SceneDescription.SIGN_UNKNOWN,
        }
        msg.direction_sign = sign_map[data['direction_sign']]

        # Дистанции — имена в JSON и в .msg совпадают
        for json_name, has_name, val_name in [
            ('stop_line_distance_m', 'has_stop_line', 'stop_line_distance_m'),
            ('turn_distance_m', 'has_turn', 'turn_distance_m'),
            ('obstacle_distance_m', 'has_obstacle', 'obstacle_distance_m'),
        ]:
            val = data.get(json_name)
            if val is None:
                setattr(msg, has_name, False)
                setattr(msg, val_name, 0.0)
            else:
                setattr(msg, has_name, True)
                setattr(msg, val_name, float(val))

        msg.confidence = float(data['confidence'])
        msg.source = data['source']
        return msg

    def process_frame(self, image_bytes=None, prompt_text=None):
        mode = self.get_parameter('mode').value
        now_s = self.get_parameter('now_s_override').value
        if now_s < 0:
            now_s = self.get_now_s()

        # Для тестов (mock) читаем из файла
        if mode == 'mock':
            with open(self.get_parameter('fixture_path').value, 'r') as f:
                raw_json = f.read()
        elif mode == 'cache':
            # Логика кэша
            image_bytes = image_bytes or b'dummy_image'
            prompt_text = prompt_text or 'dummy_prompt'
            config_dict = json.loads(
                self.get_parameter('generation_config').value)

            key = self.compute_cache_key(
                image_bytes,
                prompt_text,
                self.get_parameter('model_id').value,
                config_dict)

            cache_file = os.path.join(
                self.get_parameter('cache_dir').value, f'{key}.json')
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    raw_json = f.read()
                self.get_logger().info('Cache hit')
            else:
                if self.backend is None:
                    self.get_logger().error('Cache miss, but no backend!')
                    return
                raw_json = self.backend(image_bytes, prompt_text, config_dict)
                os.makedirs(
                    self.get_parameter('cache_dir').value,
                    exist_ok=True)
                with open(cache_file, 'w') as f:
                    f.write(raw_json)
                self.get_logger().info('Cache miss, backend called')
        else:
            self.get_logger().error('Live mode without backend is not allowed')
            return

        # Валидация и публикация
        data, reason = self.validate_and_parse(raw_json, now_s)

        if data is None:
            msg = self.make_canonical_unknown(reason)
        else:
            msg = self.json_to_ros(data)

        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SceneAdapter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
