from unittest import TestCase

from hlc.fetcher_cache import CachedObject


def init(self, *a, **ka):
    self.init = (a, ka)
    #print('Initializing {cls}: {args}'.format(cls=self.__class__.__name__, args=self.init))


class A(CachedObject):
    __init__ = init


class B(CachedObject):
    __init__ = init


class C(A):
    pass


class TestCachedObjects(TestCase):

    def test_caching(self):
        for cls in (A, B, C):
            a1 = cls('hello', 'world')
            a2 = cls(None)
            with self.subTest(cls=cls):
                self.assertIs(cls(None), a2)
                self.assertIs(cls('hello', 'world'), a1)

    def test_separate_caches(self):
        a = A(None)
        b = B(None)
        c = C(None)
        a1 = A(None)
        self.assertIsNot(a, b)
        self.assertIsNot(a, c)
        self.assertIs(a, a1)

    def test_cache_maxsize(self):
        for cls in (A, B, C):
            maxsize = cls._CACHE_SIZE
            for num in range(maxsize * 2):
                first = cls(num, num, num)
                second = cls(num, num, num)
                with self.subTest(cls=cls, num=num):
                    self.assertIs(first, second)
                    self.assertTrue(len(cls._objects) <= maxsize)
                    self.assertEqual(first.init, ((num, num, num), {}))
            for num in range(maxsize):
                cls(num)
            self.assertEqual(len(cls._objects), maxsize + 1) # one strong ref above: second

