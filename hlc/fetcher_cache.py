'''
Caching mechanism for info fetchers
'''


from collections import deque


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
        return '{cls}(maxsize={maxsize}'.format(
            cls=self.__class__.__name__,
            maxsize=self.maxsize
        )
