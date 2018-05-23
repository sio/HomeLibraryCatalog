"""
Useful utilities
"""

from . import VERBOSITY
import base64
import html
import os
import random
import re
import textwrap
from datetime import datetime
from collections import UserDict
from hashlib import sha512


class LinCrypt(object):
    """
    Simple linear function for obfuscating integers based on integer key
    Returns string (url safe)

    This is not cryptographically safe! It should be used only for obfuscating
    non-sensitive data, i.e. generating non-sequential IDs
    """
    def __init__(self, key):
        # for int operations
        key = int(key)
        k = (7, 3, 17, 4)
        self._b = 2 + key % k[0]
        self._c = sum((k[1] * (key % k[2]),
                       k[3] * self.sum_digits(key),
                       key * self._b))

        # for str operations
        in_chr  = "_0123456789ABCDEF"
        out_chr = "LZQUOXKVYGNSWJRHT"
        shift = self.sum_digits(key) % len(out_chr)
        out_chr = out_chr[shift:] + out_chr[:shift]
        first = "L"  # looks better (it occurs more often in resulting IDs)
        out_chr = first + out_chr.replace(first, "")
        self.charmap = str.maketrans(in_chr+out_chr, out_chr+in_chr)

    def int_encode(self, number):
        return int(self._b * number + self._c)

    def int_decode(self, number):
        return int((number - self._c)/self._b)

    def encode(self, number):
        hex_string = hex(self.int_encode(number)).upper()[2:][::-1]
        enc_string = self.mangle(hex_string).translate(self.charmap)
        return enc_string

    def decode(self, string):
        hex_string = self.unmangle(string.translate(self.charmap))
        int_number = self.int_decode(int("0x" + hex_string[::-1], base=16))
        return int_number

    @staticmethod
    def sum_digits(number):
        """Return sum of digits in integer"""
        number = int(number)
        if number > 0:
            return sum(int(d) for d in str(number))

    @staticmethod
    def mangle(text, streams=3, padding="_"):
        """Mix characters in a string in a reversable way"""
        if streams < 2:
            streams = 2
        if len(text) % streams:
            text = padding * (streams - len(text) % streams) + text

        words = [str(),] * streams
        for pos, char in enumerate(text):
            words[pos % streams] += char
        return "".join(words)

    @staticmethod
    def unmangle(text, streams=3, padding="_"):
        """Reverse string produced by mangle() method to original"""
        if streams < 2:
            streams = 2
        if len(text) % streams:
            raise ValueError("incorrect padding: %s" % text)

        pieces = list()
        piece_len = int(len(text) / streams)
        for s in range(streams):
            pieces.append(text[s*piece_len:(s+1)*piece_len])

        readable = str()
        for chars in zip(*pieces):
            readable += "".join(chars)
        return readable.strip(padding)


class PassHash(object):
    """
    A group of methods to create and validate password hashes with random salt
    Hashing function is easy to redefine
    """
    _delimiter = ":"  # separates hash and salt, must not occur in either one
    _salt_size = 512  # bytes

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
            salt = base64.urlsafe_b64encode(os.urandom(cls._salt_size))

        if isinstance(password, str):
            password = password.encode()
        else:
            raise TypeError("expected string, but got %s" % type(password))

        if not isinstance(salt, bytes):
            raise TypeError("expected bytes, but got %s" % type(salt))

        return cls.function(salt + password) + cls._delimiter + salt.decode()

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
        if hash:
            if hash.count(cls._delimiter) != 1:
                raise ValueError("unable to separate salt and hash")
            salt = hash.split(cls._delimiter)[1].encode()
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


class DynamicDict(UserDict):
    """
    Dictionary that can store values computable upon access

    If value stored in dictionary can be called with zero arguments, it will
    be called upon accessing and the result will be returned instead of value

    Otherwise, behaves exactly as dict
    """
    def __init__(self):
        super().__init__()
        self.__fns = set()  # functions of zero args returning dynamic values

    def __getitem__(self, key):
        value = super().__getitem__(key)
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
        super().__setitem__(key, value)

    def __delitem__(self, key):
        super().__delitem__(key)
        try:
            self.__fns.remove(key)
        except KeyError:
            pass


def timestamp():
    """Return current Unix timestamp"""
    return int(datetime.timestamp(datetime.now()))


def time2unix(time):
    """Convert local time to Unix timestamp"""
    if isinstance(time, datetime):
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

    if urgency <= VERBOSITY[0]:
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


def fuzzy_str_eq(one, two):
    """
    Check if two strings are _kinda_ the same
    """
    def simplify(text):
        return re.sub("[^\d\w]", "", text).lower()
    return (one == two or simplify(one) == simplify(two))


def parse_csv(csv):
    """
    Parse comma-separated sequence of values (one line)
    """
    items = list()
    for item in csv.split(","):
        if item: item = alphanumeric(item).strip()
        items.append(item)
    return items

def printf_replacement(text, *args):
    """
    printf replacement for older sqlite versions
    """
    return text % tuple(a if a else "" for a in args)


def render_html(raw, markup=None):
    '''Generate HTML from user input'''
    if markup is None: markup = 'plain text'

    def text2html(text):
        def paragraphs():
            newlines = re.compile(r'\s*\n\s*')
            for p in re.sub(newlines, r'\n', text).splitlines():
                yield html.escape(p.strip())
        return '\n'.join('<p>%s</p>' % p for p in paragraphs())

    renderers = {
        'plain text': text2html,
    }
    if raw:
        output = renderers[markup](raw)
    else:
        output = ''
    return output
