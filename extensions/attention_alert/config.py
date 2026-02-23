import os
import yaml
from pathlib import Path

# Default configuration
DEFAULT_CONFIG = {
    "enabled": True,
    "cooldown_seconds": 10,
    "stall_timeout_seconds": 30,
    "backends": {
        "audio": {"enabled": True},
        "desktop": {"enabled": True},
        "webhook": {"enabled": False, "url": "", "secret": ""}
    },
    "escalation": [
        {"delay_seconds": 0, "backend": "audio"},
        {"delay_seconds": 30, "backend": "desktop"},
        {"delay_seconds": 120, "backend": "webhook"},
        {"delay_seconds": 600, "action": "auto_pause"}
    ],
    "history": {
        "enabled": True,
        "db_path": "notifications.db",
        "retention_days": 30
    }
}

class Config:
    def __init__(self, config_data: dict):
        self._data = config_data

    @property
    def enabled(self) -> bool:
        return self._data.get("enabled", True)

    @property
    def cooldown_seconds(self) -> int:
        return self._data.get("cooldown_seconds", 10)

    @property
    def stall_timeout_seconds(self) -> int:
        return self._data.get("stall_timeout_seconds", 30)

    @property
    def backends(self) -> dict:
        return self._data.get("backends", {})

    @property
    def escalation(self) -> list:
        return self._data.get("escalation", [])

    @property
    def history(self) -> dict:
        return self._data.get("history", {})

    @classmethod
    def load(cls, config_path: str = None) -> 'Config':
        """Load configuration from YAML file, falling back to defaults."""
        config_data = DEFAULT_CONFIG.copy()

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    yaml_data = yaml.safe_load(f)
                    if yaml_data and "attention_alert" in yaml_data:
                        # Deep update config_data with yaml_data["attention_alert"]
                        cls._deep_update(config_data, yaml_data["attention_alert"])
            except Exception as e:
                print(f"Error loading config file {config_path}: {e}")
                # Fall back to default
                pass

        # Apply environment variable overrides (example)
        if "ALERT_COOLDOWN" in os.environ:
            try:
                config_data["cooldown_seconds"] = int(os.environ["ALERT_COOLDOWN"])
            except ValueError:
                pass
                
        # Handle secrets which should ideally come from env vars
        if "ALERT_WEBHOOK_SECRET" in os.environ:
             if "webhook" not in config_data["backends"]:
                  config_data["backends"]["webhook"] = {}
             config_data["backends"]["webhook"]["secret"] = os.environ["ALERT_WEBHOOK_SECRET"]

        return cls(config_data)
        
    @staticmethod
    def _deep_update(d: dict, u: dict):
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = Config._deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

# Global config instance
_config = None

def get_config(reload=False, config_path=None) -> Config:
    global _config
    if _config is None or reload:
        # Try to find config file if path not specified
        if not config_path:
            # Look in standard locations:
            # 1. Current directory
            # 2. Extension directory
            possible_paths = [
                "config.yaml",
                os.path.join(os.path.dirname(__file__), "config.yaml")
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break
        
        _config = Config.load(config_path)
    return _config
