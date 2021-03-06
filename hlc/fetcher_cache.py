'''
Caching mechanism for info fetchers
'''


from collections import deque
from weakref import WeakValueDictionary


class StrongCache:
    '''
    Dict-like object with a limit on number of keys

    When maximum number of keys is reached adding new keys will result in
    dropping the oldest existing keys (first in, first out)
    '''

    def __init__(self, maxsize):
        self.maxsize = maxsize
        self._queue = deque()
        self._cache = dict()

    def __setitem__(self, key, value):
        if key not in self and len(self._queue) >= self.maxsize:
            dropped = self._queue.popleft()
            del self._cache[dropped]
        elif key in self:
            self._queue.remove(key)
        self._cache[key] = value
        self._queue.append(key)

    def __getitem__(self, key):
        return self._cache[key]

    def __delitem__(self, key):
        del self._cache[key]
        self._queue.remove(key)

    def __contains__(self, key):
        return key in self._cache

    def __len__(self):
        return len(self._cache)

    def __repr__(self):
        return '<{cls} maxsize={maxsize} at {id}>'.format(
            cls=self.__class__.__name__,
            id=hex(id(self)),
            maxsize=self.maxsize
        )


class WeakAndStrongCache:
    '''
    Dict-like object with a limit on number of strongly references values

    When limit is reached the oldest values are dropped from the strong-ref
    cache (FIFO). Unlimited number of  weak references is kept while the
    corresponding objects exist.
    '''

    def __init__(self, maxsize):
        self.maxsize = maxsize
        self._weak = WeakValueDictionary()
        self._strong = StrongCache(maxsize)

    def __setitem__(self, key, value):
        self._weak[key] = value
        self._strong[key] = value

    def __getitem__(self, key):
        return self._weak[key]

    def __delitem__(self, key):
        del self._weak[key]
        del self._strong[key]

    def __contains__(self, key):
        return key in self._weak

    def __len__(self):
        return len(self._weak)

    __repr__ = StrongCache.__repr__


class CachedObjectMeta(type):
    '''
    Metaclass that enables caching instance creation for each of child classes
    '''

    def __init__(cls, name, bases, dct):
        cls._objects = WeakAndStrongCache(cls._CACHE_SIZE)

    def __call__(cls, *a, **ka):
        cache_key = (a, tuple(ka))
        if cache_key in cls._objects:
            old = cls._objects[cache_key]
            return old  # skip cls.__init__()
        else:
            new = super().__call__(*a, **ka)  # run both __new__() and __init__()
            cls._objects[cache_key] = new
            return new


class CachedObject(metaclass=CachedObjectMeta):
    '''
    An object that will cache previous instances and return them when
    initialized with the same arguments
    '''
    _CACHE_SIZE = 25
