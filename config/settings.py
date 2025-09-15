import os
import yaml
import re
from typing import Dict, Any


class Settings:
    """Configuration management for BinBot"""
    
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from config.yaml with environment variable substitution"""
        try:
            with open("config.yaml", "r") as file:
                config_content = file.read()

            # Replace environment variables
            def replace_env_var(match):
                var_name = match.group(1)
                return os.environ.get(var_name, match.group(0))

            config_content = re.sub(r'\$\{([^}]+)\}', replace_env_var, config_content)

            # Parse YAML
            config = yaml.safe_load(config_content)
            return config if config else {}

        except FileNotFoundError:
            print("Warning: config.yaml not found, using default configuration")
            return self._get_default_config()
        except yaml.YAMLError as e:
            print(f"Error parsing config.yaml: {e}")
            return self._get_default_config()
        except Exception as e:
            print(f"Unexpected error loading configuration: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "database": {
                "persist_directory": "/app/data/chromadb",
                "collection_name": "inventory"
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False
            },
            "llm": {
                "provider": "openai",
                "openai": {
                    "model": "gpt-3.5-turbo",
                    "embedding_model": "text-embedding-ada-002"
                }
            },
            "voice": {
                "provider": "browser",
                "browser": {
                    "tts_rate": 0.9,
                    "tts_pitch": 1.0,
                    "tts_volume": 0.8
                },
                "openai": {
                    "tts_model": "tts-1",
                    "tts_voice": "alloy",
                    "whisper_model": "whisper-1",
                    "audio_format": "mp3"
                }
            }
        }

    def get_voice_config(self) -> Dict[str, Any]:
        """Get voice configuration"""
        return self.config.get('voice', self._get_default_config()['voice'])
