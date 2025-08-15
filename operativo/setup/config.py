
import os
import yaml

from pathlib import Path
from types import SimpleNamespace
from dotenv import load_dotenv

from decorators.singleton import Singleton


class ConfigError(Exception):
    """Raised when a configuration value is wrong"""
    pass


@Singleton
class GlobalConfig:

    def __init__(self):
        self.app_config: SimpleNamespace = SimpleNamespace()
        self.load_config_files()

    def load_config_files(self):

        # cargar variables de entorno
        load_dotenv(override=True)

        # Definir carpeta de los archivos a leer
        files_path: Path = Path(__file__).parent.resolve()

        # Leer archivos de configuración
        with open(f'{files_path}/config.yaml', 'r') as f:
            self.app_config = yaml.safe_load(f.read())

        # Expandir variables de entorno
        self.app_config = self.expand_env_vars(self.app_config)

        # Permitir acceder a las configuraciones con puntos
        self.app_config = self.dict_to_namespace(self.app_config)

    def expand_env_vars(self, d: dict | list | str):
        """ Iterate recursively through dictionaries, expanding any string. """
        if isinstance(d, dict):
            return {key: self.expand_env_vars(value) for key, value in d.items()}
        elif isinstance(d, list):
            return [self.expand_env_vars(item) for item in d]
        elif isinstance(d, str):
            return os.path.expandvars(d)
        else:
            return d

    def dict_to_namespace(self, d: dict) -> SimpleNamespace:
        """ Iterate recursively through dictionaries, transforming keys and values to SimpleNamespace. """
        x = SimpleNamespace()
        _ = [setattr(x, k, self.dict_to_namespace(v))
             if isinstance(v, dict) else setattr(x, k, v) for k, v in d.items()]
        return x
