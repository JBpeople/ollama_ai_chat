import os
import platform

def get_config_path():
    if platform.system() == 'Darwin':  # macOS
        config_dir = os.path.expanduser('~/Library/Application Support/OllamaAIChat')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        return os.path.join(config_dir, 'config.ini')
    else:  # Windows or other
        return "config.ini"

CONFIG_FILE = get_config_path()
DEFAULT_SERVER = "50.126.45.75:11434"
DEFAULT_TIMEOUT = 60.0