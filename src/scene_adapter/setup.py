from glob import glob

from setuptools import find_packages, setup

package_name = 'scene_adapter'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
        ('share/' + package_name + '/contracts', glob('contracts/*.json')),
        ('share/' + package_name + '/fixtures', glob('fixtures/vlm/*.json')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='naskok',
    maintainer_email='nado.09.ru@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'scene_adapter_node = scene_adapter.node:main',
        ],
    },
)
