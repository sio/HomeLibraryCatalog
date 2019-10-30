import random
from unittest import TestCase

from hlc.fetcher_cache import StrongCache


class StrongCacheTests(TestCase):

    def setUp(self):
        maxsize = random.randint(10, 50)
        self.cache = StrongCache(maxsize)

    def test_maxsize(self):
        maxsize = self.cache.maxsize
        for num in range(maxsize * 5):
            with self.subTest(num=num):
                self.cache[num] = None
                self.assertTrue(len(self.cache) <= maxsize)
                if num > maxsize:
                    self.assertNotIn(num - maxsize, self.cache)
                elif num > 1:
                    self.assertIn(num - 1, self.cache)

    def test_repeat_insert(self):
        maxsize = self.cache.maxsize
        keys = list(range(maxsize))
        for num in keys:
            self.cache[num] = None
        for num in sorted(keys, key=lambda x: random.random()):
            self.cache[num] = 1
            with self.subTest(num=num):
                self.assertEqual(num, self.cache._queue[-1])
                self.assertEqual(maxsize, len(self.cache))
                self.assertEqual(maxsize, len(self.cache._queue))

    def test_delete(self):
        maxsize = self.cache.maxsize
        keys = list(range(maxsize))
        for num in keys:
            self.cache[num] = None
        deleted = set()
        for _ in range(int(maxsize/2)):
            length = len(self.cache)
            while True:
                num = random.choice(keys)
                if num not in deleted:
                    deleted.add(num)
                    break
            with self.subTest(num=num):
                self.assertIn(num, self.cache)
                del self.cache[num]
                self.assertNotIn(num, self.cache)
                self.assertEqual(len(self.cache), length - 1)
