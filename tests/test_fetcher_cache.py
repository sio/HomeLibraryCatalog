import random
from unittest import TestCase

from hlc.fetcher_cache import StrongCache, WeakAndStrongCache


class Dummy:
    '''Dummy value that may be weakly referenced'''
    def __init__(self, value):
        self.value = value


class TestStrongCache(TestCase):

    def setUp(self):
        maxsize = random.randint(10, 50)
        self.cache = StrongCache(maxsize)

    def test_maxsize(self):
        '''Check that size limit is maintained'''
        maxsize = self.cache.maxsize
        for num in range(maxsize * 5):
            with self.subTest(num=num):
                self.cache[num] = Dummy(None)
                self.assertTrue(len(self.cache) <= maxsize)
                if num > maxsize:
                    self.assertNotIn(num - maxsize, self.cache)
                elif num > 1:
                    self.assertIn(num - 1, self.cache)

    def test_repeat_insert(self):
        '''Check that repeated inserts bump cache key priority'''
        maxsize = self.cache.maxsize
        keys = list(range(maxsize))
        for num in keys:
            self.cache[num] = Dummy(None)
        for num in sorted(keys, key=lambda x: random.random()):
            self.cache[num] = Dummy('123')
            with self.subTest(num=num):
                self.assertEqual(num, self.cache._queue[-1])
                self.assertEqual(maxsize, len(self.cache))
                self.assertEqual(maxsize, len(self.cache._queue))

    def test_delete(self):
        '''Test deleting items from cache'''
        maxsize = self.cache.maxsize
        keys = list(range(maxsize))
        for num in keys:
            self.cache[num] = Dummy(None)
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
                self.assertEqual(len(self.cache._queue), length - 1)


class TestWeakAndStrongCache(TestStrongCache):
    '''Run all tests for TestStrongCache also'''

    def setUp(self):
        maxsize = random.randint(25, 100)
        self.cache = WeakAndStrongCache(maxsize)
        self.cache._queue = self.cache._strong._queue  # API compatibility with StrongCache

    def test_weakref_add(self):
        strong_ref = Dummy('hello')
        maxsize = self.cache.maxsize
        self.cache[-1] = strong_ref
        for num in range(maxsize):
            self.cache[num] = Dummy('world')
        self.assertEqual(len(self.cache), maxsize + 1)
        del strong_ref
        self.assertEqual(len(self.cache), maxsize)

    def test_weakref_many(self):
        strong_ref = Dummy('hello')
        strong_ref_count = 0
        maxsize = self.cache.maxsize
        for num in range(maxsize):
            self.cache[num] = strong_ref
            strong_ref_count += 1
        for num in range(maxsize, maxsize * 10):
            if random.randint(0, 3):
                self.cache[num] = Dummy('weakref')
            else:
                self.cache[num] = strong_ref
                strong_ref_count += 1
        for num in range(maxsize * 10, maxsize * 11):
            # Make sure only weakrefs are queued at the end of the test
            self.cache[num] = Dummy('weakref')
        self.assertEqual(len(self.cache), strong_ref_count + maxsize)
        length = len(self.cache)
        del strong_ref
        self.assertEqual(len(self.cache), length - strong_ref_count)
