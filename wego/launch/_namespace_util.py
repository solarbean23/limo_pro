import os

import yaml
from ament_index_python.packages import get_package_share_directory


def load_namespace_config():
    config_path = os.path.join(
        get_package_share_directory('wego'), 'config', 'namespace.yaml'
    )
    with open(config_path, 'r', encoding='utf-8') as config_file:
        return yaml.safe_load(config_file) or {}


def robot_namespace(config=None):
    config = config or load_namespace_config()
    namespace = config.get('robot', {}).get('namespace', '')
    return str(namespace).strip('/')


def topic_name(key, default, config=None):
    config = config or load_namespace_config()
    value = config.get('topics', {}).get(key, default)
    return str(value).strip('/')


def frame_name(key, default, config=None, *, prefix=True):
    config = config or load_namespace_config()
    value = str(config.get('frames', {}).get(key, default)).strip('/')
    if not prefix or key == 'map':
        return value

    namespace = robot_namespace(config)
    return f'{namespace}/{value}' if namespace else value


def tf_prefix(config=None):
    namespace = robot_namespace(config)
    return f'{namespace}/' if namespace else ''


def namespace_env(config=None):
    namespace = robot_namespace(config)
    return {'LIMO_NAMESPACE': namespace} if namespace else {}
