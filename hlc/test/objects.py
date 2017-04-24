"""
Unit tests for HomeLibraryCatalog
"""

import unittest


from hlc.web import ISBN
class testISBN(unittest.TestCase):
    def test_X(self):
        self.assertEqual(ISBN("123-456-789-012-X").valid, True)

    def test_X2(self):
        self.assertEqual(ISBN("123-456-789-X-012").valid, False)

    def test_X3(self):
        self.assertEqual(ISBN("123-456-789-012-x").valid, True)

    def test_X4(self):
        self.assertEqual(ISBN("123-456-7-012-XXX").valid, False)

    def test_value_setter(self):
        i = ISBN("")
        i.value = "1231231231"
        self.assertEqual(i._valid, None)
        self.assertEqual(i.valid, True)


from hlc.web import CatalogueDB
class testCatalogueDB(unittest.TestCase):
    def setUp(self):
        self.dbapi = CatalogueDB(":memory:")

    def tearDown(self):
        del self.dbapi

    def test_created(self):
        valid = type(self.dbapi) is CatalogueDB
        self.assertTrue(valid)
