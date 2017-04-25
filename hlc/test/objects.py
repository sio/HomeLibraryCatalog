"""
Unit tests for HomeLibraryCatalog
"""

import unittest


from hlc.web import ISBN
class testISBN(unittest.TestCase):
    def test_valid(self):
        for text, status in (
            ("123-456-789-012-X", True),
            ("123-456-789-X-012", False),
            ("123-456-789-012-x", True),
            ("123-456-7-012-XXX", False),
        ):
            with self.subTest(text=text, status=status):
                self.assertEqual(ISBN(text).valid, status)

    def test_value_setter(self):
        i = ISBN("")
        i.value = "1231231231"
        self.assertEqual(i._valid, None)
        self.assertEqual(i.valid, True)


from hlc.web import CatalogueDB
class testCatalogueDB(unittest.TestCase):
    """New SQLite database is created in memory for each test"""
    def setUp(self):
        self.dbapi = CatalogueDB(":memory:")

    def tearDown(self):
        del self.dbapi

    def test_created(self):
        self.assertIs(type(self.dbapi), CatalogueDB)
