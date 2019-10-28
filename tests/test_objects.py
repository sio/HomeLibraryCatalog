"""
Unit tests for HomeLibraryCatalog
"""

import unittest


from hlc.util import LinCrypt, random_str
import random
class testLinCrypt(unittest.TestCase):
    def test_mangle(self):
        for i in range(100):
            word = random_str(5,50)
            streams = random.randint(2,10)
            with self.subTest(word=word):
                self.assertEqual(
                    LinCrypt.unmangle(LinCrypt.mangle(word, streams), streams),
                    word)

    def test_consistent(self):
        for i in range(10):
            key = random.randint(0, 2**32)
            number = random.randint(0, 2**32)
            hidden = LinCrypt(key).encode(number)
            for repeat in range(10):
                with self.subTest(k=key, n=number, v=hidden):
                    self.assertEqual(
                        hidden,
                        LinCrypt(key).encode(number))

    def test_reversable(self):
        for i in range(100):
            number = random.randint(0, 2**32)
            key = random.randint(2**10, 2**32)
            with self.subTest(number=number, key=key):
                self.assertEqual(
                    number,
                    LinCrypt(key).decode(LinCrypt(key).encode(number)))


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

    def test_barcode_create(self):
        from hlc.items import Barcode
        b = Barcode(self.db)
        b.isbn = 1231231231
        b.save()

    def test_barcode(self):
        from hlc.items import Barcode
        numbers = {
            "123456789-0": True,
            1234567890: True,
            123: False,
            "123": False,
            "isbn": False,
            None: False}
        for isbn, valid in numbers.items():
            with self.subTest(isbn=isbn):
                b = Barcode(self.db)
                if valid:
                    b.isbn = isbn
                    b.save()
                    self.assertEqual(b.isbn, ISBN(isbn).number)
                    b.delete()
                else:
                    with self.assertRaises(ValueError):
                        b.isbn = isbn
