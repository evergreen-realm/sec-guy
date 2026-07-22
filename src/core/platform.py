"""
Cross-platform path and environment abstraction.
"""

from pathlib import Path
import os
import platform


class Platform:
    @staticmethod
    def get_os() -> str:
        return platform.system().lower()

    @staticmethod
    def get_project_root() -> Path:
        return Path(__file__).parent.parent.parent

    @staticmethod
    def get_config_dir() -> Path:
        os_name = Platform.get_os()
        if os_name == 'windows':
            return Path(os.environ.get('APPDATA', 'C:\\')) / 'sec-guy'
        else:
            return Path('/etc') / 'sec-guy'

    @staticmethod
    def get_vault_dir() -> Path:
        os_name = Platform.get_os()
        if os_name == 'windows':
            return Path(os.environ.get('TEMP', 'C:\\Temp')) / 'secguy-vault'
        else:
            return Path('/dev/shm') / 'secguy-vault'

    @staticmethod
    def get_log_dir() -> Path:
        os_name = Platform.get_os()
        if os_name == 'windows':
            return Path(os.environ.get('APPDATA', 'C:\\')) / 'sec-guy' / 'logs'
        else:
            return Path('/var/log') / 'sec-guy'