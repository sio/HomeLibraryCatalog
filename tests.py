#!/usr/bin/python3
# -*- coding: utf-8 -*-

import unittest

from hlc.web import ISBN
class TestISBN(unittest.TestCase):
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

        
if __name__ == "__main__":
    unittest.main(exit=False)

