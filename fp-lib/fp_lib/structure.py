
class LastNList(object):
    """A list structure that keeps the latest N arrays
    Always save at most N items. when adding the N+1th item, the oldest item
    will be discarded.
    E.g.

    >>> l = LastNList(2)
    >>> l.put(1)
    >>> l.put(2)
    >>> l.all()
    [1, 2]
    >>> l.put(3)
    >>> l.all()
    [2, 3]
    >>> l.put(4)
    >>> l.all()
    [3, 4]
    """

    def __init__(self, size, reserve=None):
        """
        By default, one time of the specified size is reserved
        """
        self.size = size
        self._data = []
        self._index = 0
        self.reserve = reserve if (reserve and reserve >= self.size) \
            else self.size * 2

    def append(self, item):
        if len(self._data) >= self.reserve:
            del self._data[:self._index + 1]
            self._index = 0
        elif len(self._data) >= self.size:
            self._index += 1
        self._data.append(item)

    def get(self, index=None):
        return self._data[self._index + index]

    def all(self):
        return self._data[self._index:]

    def clean(self):
        del self._data[:]

    def __str__(self):
        return str(self.all())
