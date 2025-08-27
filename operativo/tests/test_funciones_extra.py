
import unittest
import datetime as dt

from calendar import Day

from funciones_extra import get_date_for_weekday


class ItemTest(unittest.TestCase):

    def setUp(self):
        self.wednesday = dt.datetime(2025, 8, 20)
        self.friday = dt.datetime(2025, 8, 22)
        self.sunday = dt.datetime(2025, 8, 17)

    def test_get_date_for_weekday(self):
        self.assertEqual(self.wednesday, get_date_for_weekday(self.friday, Day.WEDNESDAY),
                         'Error al definir miércoles previo')
        self.assertEqual(self.sunday, get_date_for_weekday(self.wednesday, Day.SUNDAY),
                         'Error al definir domingo previo')


if __name__ == "__main__":
    unittest.main()
