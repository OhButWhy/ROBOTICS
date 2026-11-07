from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


def _expand_urdf():
    xacro_path = Path(__file__).parent.parent / 'urdf' / 'vehicle.urdf.xacro'
    result = subprocess.run(
        ['xacro', str(xacro_path)],
        capture_output=True, text=True, check=True,
    )
    return ET.fromstring(result.stdout)


def _find_joint_by_child(root, child_link):
    for joint in root.findall('joint'):
        child = joint.find('child')
        if child is not None and child.get('link') == child_link:
            return joint
    return None


def test_lidar_parent_is_base_link():
    """Лідар должен крепиться к base_link, а не к другому звену."""
    root = _expand_urdf()
    joint = _find_joint_by_child(root, 'lidar_link')
    assert joint is not None, 'lidar_link не найден в URDF'
    parent = joint.find('parent')
    assert parent is not None, 'у lidar_joint нет parent'
    assert parent.get('link') == 'base_link', (
        f'lidar_link должен крепиться к base_link, '
        f'но parent = {parent.get("link")}'
    )


def test_camera_parent_is_base_link():
    root = _expand_urdf()
    joint = _find_joint_by_child(root, 'camera_link')
    assert joint is not None
    assert joint.find('parent').get('link') == 'base_link'


def test_imu_parent_is_base_link():
    root = _expand_urdf()
    joint = _find_joint_by_child(root, 'imu_link')
    assert joint is not None
    assert joint.find('parent').get('link') == 'base_link'


def test_all_links_present():
    root = _expand_urdf()
    links = {link.get('name') for link in root.findall('link')}
    for expected in [
        'base_link',
        'camera_link',
        'lidar_link',
        'imu_link',
        'front_left_knuckle', 'front_left_wheel',
        'front_right_knuckle', 'front_right_wheel',
        'rear_left_wheel', 'rear_right_wheel',
    ]:
        assert expected in links, f'отсутствует звено {expected}'
