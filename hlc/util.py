"""
Useful utilities
"""

from hlc import VERBOSITY
import os
import re
import textwrap
import base64
from datetime import datetime
from hashlib import sha512
import random


class LinCrypt(object):
    """
    Simple linear function for obfuscating integers based on integer key

    Returns string containing hexademical integer
    """
    def __sum_digits(number):
        """Return sum of digits in integer"""
        number = int(number)
        if number > 0:
            return sum(int(d) for d in str(number))

    def __init__(self, key):
        key = int(key)
        k = (7, 3, 17, 4)
        self.__b = 2 + key % k[0]
        self.__c = sum((k[1] * (key % k[2]),
                        k[3] * type(self).__sum_digits(key),
                        key))

    def int_encode(self, number):
        return int(self.__b * number + self.__c)

    def int_decode(self, number):
        return int((number - self.__c)/self.__b)

    def encode(self, number):
        return hex(self.int_encode(number)).upper()[2:][::-1]

    def decode(self, string):
        return self.int_decode(int("0x" + string[::-1], base=16))


class PassHash(object):
    """
    A group of methods to create and validate password hashes with random salt
    Hashing function is easy to redefine
    """
    __delimiter = ":"  # separates hash and salt, must not occur in either one
    __salt_size = 512  # bytes

    @staticmethod
    def function(bytestring):
        """Hashing function"""
        f = lambda x: sha512(x).hexdigest()
            # SHA-512 is not as good as KDF, but it's available from
            # Python standard library which makes deployment easier
        return f(bytestring)

    @classmethod
    def get(cls, password, salt=None):
        """
        Get a hash string for password

        Arguments:
            password
                String. A password to hash
            salt
                Bytes. Leave this None if you want to create new hash.
                To be used only internally to validate previously created hashes
        """
        if salt is None:
            salt = base64.urlsafe_b64encode(os.urandom(cls.__salt_size))

        if type(password) is str:
            password = password.encode()
        else:
            raise TypeError("expected string, but got %s" % type(password))

        if type(salt) is not bytes:
            raise TypeError("expected bytes, but got %s" % type(salt))

        return cls.function(salt + password) + cls.__delimiter + salt.decode()

    @classmethod
    def check(cls, password, hash):
        """
        Validate password against its saved hash

        Arguments:
            password
                String. Password to check
            hash
                String. A hash of valid password
        """
        if hash.count(cls.__delimiter) != 1:
            raise ValueError("unable to separate salt and hash")
        salt = hash.split(cls.__delimiter)[1].encode()
        return hash == cls.get(password, salt)


class ReadOnlyDict(object):
    """Make dict-like object read-only"""
    def __init__(self, dictionary):
        self.__dict = dictionary
    def __getitem__(self, key):
        return self.__dict[key]
    def __contains__(self, key):
        return key in self.__dict
    def get(self, *a, **kw):
        return self.__dict.get(*a, **kw)
    def __eq__(self, other):
        return self.__dict == other
    def __iter__(self, *a, **kw):
        return self.__dict.__iter__(*a, **kw)
    def __len__(self, *a, **kw):
        return self.__dict.__len__(*a, **kw)
    def __repr__(self, *a, **kw):
        return self.__dict.__repr__(*a, **kw)
    def __str__(self, *a, **kw):
        return self.__dict.__str__(*a, **kw)
    def keys(self, *a, **kw):
        return self.__dict.keys(*a, **kw)


class DynamicDict(dict):
    """
    Dictionary that can store values computable upon access

    If value stored in dictionary can be called with zero arguments, it will
    be called upon accessing and the result will be returned instead of value

    Otherwise, behaves exactly as dict
    """
    def __init__(self):
        dict.__init__(self)
        self.__fns = set()  # functions of zero args returning dynamic values

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        if key in self.__fns:
            return value()
        else:
            return value

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key, value):
        try:
            value()
            self.__fns.add(key)
        except TypeError:  # value not callable or requires arguments
            try:  # remove function key if it was left behind somehow
                self.__fns.remove(key)
            except KeyError:
                pass
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        try:
            self.__fns.remove(key)
        except KeyError:
            pass


def timestamp():
    """Return current Unix timestamp"""
    return int(datetime.timestamp(datetime.now()))


def time2unix(time):
    """Convert local time to Unix timestamp"""
    if type(time) == datetime:
        return int(datetime.timestamp(time))
    else:
        raise ValueError("%s is not %s object" % (time, datetime))


def unix2time(unix):
    """Conver Unix timestamp to local time"""
    return datetime.fromtimestamp(float(unix))


def message(text, urgency=5):
    """
    Print messages to standard output.

    Urgency:
        0: very important,
        5: normal messages,
        9: debug messages
    """
    if urgency < 0:
        urgency = 0

    text = str(text)

    if urgency <= VERBOSITY:
        indentation = chr(183) * urgency + " "
        wr = textwrap.TextWrapper(initial_indent=indentation,
                                  subsequent_indent=indentation)
        for line in text.splitlines():
            for short_line in wr.wrap(line):
                print(short_line)


def debug(*args):
    for text in args:
        message(text, 9)


def random_str(min, max=None):
    """
    Return random ASCII string (letters+digits)

    Arguments:
        min
            Integer. Minimum string length
        max
            Integer, optional. Maximum string length. If both `min` and `max`
            are specified returned string will be of random length between these
            two values
    """
    ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    length = 0
    if max is None:
        length = int(min)
    elif max >= min:
        length = random.SystemRandom().randint(int(min), int(max))
    else:
        raise ValueError("Invalid minimum and maximum combination: %s, %s" %
             (min, max))
    return "".join(random.SystemRandom().choice(ALPHABET) for i in range(length))


def lowercase(string):
    """
    Returns a string in lower case. To be used instead of SQLITE built-in
    that can't handle cyrillic letters
    """
    if string:
        return str(string).lower()


def alphanumeric(string):
    """
    Returns only alphanumeric characters from string. To be used in SQLITE
    """
    if string:
        string = re.sub("\s+", " ", string)
        string = re.sub("[^\d\w ]", "", string)
        return string.strip()
