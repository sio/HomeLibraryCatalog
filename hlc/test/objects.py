"""
Unit tests for HomeLibraryCatalog
"""

import unittest

import hlc.util

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
        self.db = CatalogueDB(":memory:")

    def tearDown(self):
        del self.db

    def test_created(self):
        self.assertIs(type(self.db), CatalogueDB)

    def test_delete(self):
        def count_books():
            query = "SELECT id FROM books"
            search = self.db.sql.generic(self.db.connection, query)
            return len(list(search.fetchall()))
        for i in range(10):
            with self.subTest(creating=i):
                b = self.db.getbook()
                b.name = "Test Name"
                b.save()
                self.assertEqual(count_books(), i+1)
        for i in range(10, 0, -1):
            with self.subTest(deleting=i):
                b = self.db.getbook(i)
                b.delete()
                self.assertEqual(count_books(), i-1)

    def test_unusable_after_delete(self):
        b = self.db.getbook()
        b.delete()
        for no, fn in enumerate((
            lambda: b.delete(),
            lambda: b.id,
            lambda: b.name,
            lambda: b.saved,
        )):
            with self.subTest(no=no+1, fn=fn):
                self.assertRaises(AttributeError, fn)
