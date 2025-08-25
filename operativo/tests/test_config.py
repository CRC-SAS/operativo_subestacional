
import unittest

from setup.config import GlobalConfig
from script import ScriptControl


class ItemTest(unittest.TestCase):

    def setUp(self):
        self.config = GlobalConfig.Instance()

    def test_read(self):
        self.assertIsNotNone(self.config.app_config)

    def test_log_level(self):
        if getattr(self.config.app_config, 'log_levels', None) is not None:
            self.assertIn(self.config.app_config.log_level, ScriptControl.valid_log_levels)

    def test_mandatory_data(self):
        self.assertIsNotNone(getattr(self.config.app_config, 'carpeta_datos', None))
        self.assertIsNotNone(getattr(self.config.app_config, 'carpeta_figuras', None))
        self.assertIsNotNone(getattr(self.config.app_config, 'corregir', None))
        self.assertIsNotNone(getattr(self.config.app_config, 'desc_variables', None))
        self.assertIsNotNone(getattr(self.config.app_config.desc_variables, 'pr', None))
        self.assertIsNotNone(getattr(self.config.app_config.desc_variables, 'tas', None))
        self.assertIsNotNone(getattr(self.config.app_config, 'mapeo_variables', None))
        self.assertIsNotNone(getattr(self.config.app_config.mapeo_variables, 'pr', None))
        self.assertIsNotNone(getattr(self.config.app_config.mapeo_variables, 'tas', None))
        self.assertIsNotNone(getattr(self.config.app_config.mapeo_variables, 'tasmin', None))
        self.assertIsNotNone(getattr(self.config.app_config.mapeo_variables, 'tasmax', None))
        self.assertIsNotNone(getattr(self.config.app_config.mapeo_variables, 'zg', None))
        self.assertIsNotNone(getattr(self.config.app_config, 'fechas_gmao', None))


if __name__ == "__main__":
    unittest.main()
