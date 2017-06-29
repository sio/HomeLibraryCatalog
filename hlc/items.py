"""
Items corresponding to real world objects and entities
"""

import sqlite3
import json
import re
import io
from PIL import Image
from hlc.util import debug, unix2time, time2unix, PassHash
from datetime import datetime


class NoneMocker(object):
    """
    Mock object that mimics None but with callable attributes
    """
    def __getattribute__(self, attr):
        return self
    def __call__(self, *a, **kw):
        return None
    def __bool__(self):
        return bool()
    def __str__(self):
        return str()
    def __int__(self):
        return int()
    def __len__(self):
        return 0

class TableEntityWithID(object):
    """
    Base class for entities represented by a single row in the single table,
    such as books, authors, etc.

    Properties:
        database:  Read only. CatalogueDB() object
        id:        Integer, read-only. ID of the database entry
        saved:     Boolean, read-only. Shows whether the book was modified
        json:      String, read-only. Dump object's data to JSON string

    Methods:
        save():              Saves changes to the database. Returns nothing
        getconnected(class): Returns all connected objects of type `class`
        getconnected_id(cl): Returns ids of all connected objects of type `cl`
                             Saves SQL calls compared to `getconnected` method
        isconnected(object): Check if `object` is connected
        connect(object):     Create database connection between two
                             TableEntityWithID objects. Returns nothing
        disconnect(object):  Remove database connection between two
                             TableEntityWithID objects. Returns nothing
    """
    __TableName__ = None
    __IDField__ = None

    def __getattribute__(self, attr):
        def getattr_direct(instance, attr):
            cls = object  # parent class name
            return cls.__getattribute__(instance, attr)

        # Fetch _data from database only when absolutely necessary
        if (not getattr_direct(self, "_fetched")) \
        and ((attr == "_data") \
        or  ((attr in type(self).__dict__) \
        and (isinstance(getattr(type(self), attr, None), property)))):
            getattr_direct(self, "_fetch")()

        return getattr_direct(self, attr)

    def __init__(self, db, id=None):
        if id is None:
            self._new = True
            self._saved = False
            self._fetched = True
            self._data = dict()
        else:
            self._new = False
            self._saved = True
            self._fetched = False
            # self._data is initialized upon access by _fetch() method
        self._db = db
        self._id = id
        self._changes = dict()

    def __str__(self):
        return self.json

    def __eq__(self, other):
        try:
            return (type(self) == type(other)) \
                and (self.id == other.id) \
                and (self.__TableName__ == other.__TableName__) \
                and (self.__IDField__ == other.__IDField__) \
                and (self.database == other.database)
        except Exception:
            return False

    def _fetch(self):
        if self.id is not None:
            c = self.database.sql.select(self.__TableName__,
                          {self.__IDField__: self.id})
            keys = tuple([x[0] for x in c.description])
            values = c.fetchone()
            if values:
                self._data = dict(zip(keys, values))
            else:
                raise ValueError("Item with %s=%s not found in %s"
                                 % (self.__IDField__,
                                    self.id,
                                    self.__TableName__))
        else:
            self._data = dict()
        self._fetched = True

    def _field_attr(*args):
        """Returns a single ready to use property based on the database field"""
        if len(args) == 1:    # (property_name): called as Class method
            property_name = args[0]
        elif len(args) == 2:  # (self,property_name): called as instance method
            property_name = args[1]
        else:
            raise TypeError("_field_attr() takes 1 or 2 arguments but %s were given"
                            % len(args))

        def property_set(self, value):
            if not value:
                value = None
            if type(value) is str:
                value = value.strip()
                value = re.sub("[^\S\r\n]+", " ", value)
            if (not self._new and self._data[property_name] != value) \
            or (self._new):
                self._changes[property_name] = value
                self._saved = False

        def property_get(self):
            if self._data:
                return self._data[property_name]

        return property(property_get, property_set)

    def _simple_attrs(cls, *args):
        """Create one or several simple properties"""
        for i in args:
            i = str(i)
            if not hasattr(type(cls), i):
                setattr(type(cls), i, cls._field_attr(i))

    def _date_attr(*args):
        """
        Returns a single ready to use property based on the database field
        for storing unix timestamps
        """
        if len(args) == 1:    # (property_name): called as Class method
            property_name = args[0]
        elif len(args) == 2:  # (self,property_name): called as instance method
            property_name = args[1]
        else:
            raise TypeError("_date_attr() takes 1 or 2 arguments but %s were given"
                            % len(args))

        def date_get(self):
            if self._data:
                if self._data[property_name]:
                    return unix2time(self._data[property_name])

        def date_set(self, value):
            if value:
                value = time2unix(value)
            else:
                value = None
            if self._new \
            or (not self._new and self._data[property_name] is None) \
            or (not self._new and int(self._data[property_name]) != int(value)):
                self._changes[property_name] = value
                self._saved = False

        return property(date_get, date_set)

    def _simple_date_attrs(cls, *args):
        """Create one or several simple date properties"""
        for i in args:
            i = str(i)
            if not hasattr(type(cls), i):
                setattr(type(cls), i, cls._date_attr(i))

    @property
    def database(self):
        return self._db

    @property
    def id(self):
        return self._id

    @property
    def json(self):
        return json.dumps(self._data, indent=4, ensure_ascii=False)

    @property
    def saved(self):
        return self._saved

    def save(self):
        for key in list(self._changes.keys()):
            if not self._changes[key]:
                self._changes.pop(key)
        if not self.saved and len(self._changes) > 0:
            if self._new:
                rowid = self.database.sql.insert(self.__TableName__,
                                   self._changes)
                selected = self.database.sql.select(self.__TableName__,
                                        {"_rowid_": rowid}, self.__IDField__)
                self._id = selected.fetchone()[0]
            else:
                self.database.sql.update_where(self.__TableName__,
                                 self._changes, {self.__IDField__: self.id})
            self._saved = True
            self._new = False
            self._fetched = False
            self._changes = dict()
        elif not self.saved and len(self._changes) == 0 and not self._new:
            self._saved = True

    def _connect_info(a, b):
        """
        Information for connecting pairs of objects
        """
        objects = set()
        for i in (a, b):
            if type(i) is type:
                objects.add(i)
            else:
                objects.add(type(i))

        columns = dict()
        if objects == {Book, Author}:
            unity_table = "book_authors"
            columns[Book] = "book_id"
            columns[Author] = "author_id"
        elif objects == {Book, Series}:
            unity_table = "book_series"
            columns[Book] = "book_id"
            columns[Series] = "series_id"
        elif objects == {Book, Thumbnail}:
            unity_table = "books"
            columns[Thumbnail] = "thumbnail_id"
        elif objects == {Book, BookReview}:
            unity_table = "book_reviews"
            columns[Book] = "book_id"
        elif objects == {Author, AuthorRating}:
            unity_table = "author_ratings"
            columns[Author] = "author_id"
        elif objects == {User, BookReview}:
            unity_table = "book_reviews"
            columns[User] = "reviewed_by"
        elif objects == {User, AuthorRating}:
            unity_table = "author_ratings"
            columns[User] = "rated_by"
        elif objects == {User, Group}:
            unity_table = "user_groups"
            columns[User] = "user_id"
            columns[Group] = "group_id"
        elif objects == {Book, BookFile}:
            unity_table = "book_files"
            columns[Book] = "book_id"
            columns[BookFile] = "file_id"
        elif objects == {Book, Tag}:
            unity_table = "book_tags"
            columns[Book] = "book_id"
            columns[Tag] = "tag_id"
        elif objects == {Barcode, User}:
            unity_table = "barcode_queue"
            columns[User] = "user_id"
        else:
            raise TypeError("Incompatible objects: %s, %s" %
                            tuple(objects))

        return unity_table, columns

    def isconnected(self, other):
        """
        Check if two TableEntityWithID objects are connected
        Returns boolean
        """
        if not self.database == other.database:
            raise ValueError("Objects from different databases:\n %s\n %s" %
                            (self.database, other.database))

        objects = dict()
        for i in (self, other):
            objects[type(i)] = i
        unity_table, columns = self._connect_info(other)

        data = dict()
        for i in objects.keys():
            if i in columns:
                data[columns[i]] = objects[i].id
            else:
                data[objects[i].__IDField__] = objects[i].id

        search = self.database.sql.select(unity_table, data)
        found = search.fetchone()
        return bool(found)

    def getconnected(self, cls, order=None, desc=False):
        """
        Get connected objects of type `cls`
        Returns a sequence of objects.
        If `order` is specified, results will be sorted on `order` attr of
        returned objects
        """
        ids = self.getconnected_id(cls)
        def connections():
            for id in ids:
                yield cls(self.database, id)
        if ids and not order:
            return connections()
        elif ids and order:
            return sorted(
                connections(),
                key=lambda x: getattr(x, order),
                reverse=desc)
        else:
            return list()  # boolean value is False

    def getconnected_id(self, cls):
        """
        Get connected objects of type `cls`
        Returns a tuple of ids
        """
        unity_table, columns = self._connect_info(cls)

        where = dict()
        if type(self) in columns:
            where[columns[type(self)]] = self.id
        else:
            where[self.__IDField__] = self.id  # `self`to1 relation.
                                               # Can be handled without
                                               # an extra SELECT.
                                               # Leaving as it is just in case

        what = str()
        if cls in columns:
            what = columns[cls]
        else:
            what = cls.__IDField__

        search = self.database.sql.select(unity_table, where, what)
        result = search.fetchall()

        found = list()
        if len(result):
            for i in result:
                if i[what]:
                    found.append(i[what])
        return tuple(found)

    def connect(self, other, *args):
        """
        Connect two TableEntityWithID objects in the database. Both objects have
        to be saved prior to creating connection

        *args may contain extra information required to connect certain types of
        entries, e.g. number of the book in the series
        """

        if self.isconnected(other) and len(args) == 0:
            return

        objects = dict()
        for i in (self, other):
            if not i.saved:
                raise ValueError("%s object not saved before connecting" % type(i))
            objects[type(i)] = i

        unity_table, columns = self._connect_info(other)

        data = dict()
        extra_data = dict()
        if Book in objects and Series in objects:
            if len(args) > 0:
                data["book_number"] = args[0]
                extra_data["book_number"] = args[0]

        where = dict()
        for i in objects.keys():
            if i in columns:
                data[columns[i]] = objects[i].id
            else:
                where[objects[i].__IDField__] = objects[i].id

        if len(columns) == 2:
            try:
                self.database.sql.insert(unity_table, data)
            except sqlite3.IntegrityError as e:
                if len(extra_data) > 0:
                    for i in extra_data:
                        data.pop(i)
                    count = self.database.sql.update_where(
                                             unity_table, extra_data, data)
                    if count <= 0:
                        raise e
                else:
                    raise e
        elif len(columns) == 1:
            self.database.sql.update_where(unity_table, data, where)

    def disconnect(self, other):
        """
        Remove a connection between two database entries
        """
        if not self.isconnected(other):
            return

        objects = dict()
        for i in (self, other):
            if not i.saved:
                raise ValueError("%s object not saved before disconnecting" % type(i))
            objects[type(i)] = i

        unity_table, columns = self._connect_info(other)

        data = dict()
        none_data = dict()
        where = dict()

        for i in objects.keys():
            if i in columns:
                data[columns[i]] = objects[i].id
                none_data[columns[i]] = None
            else:
                where[objects[i].__IDField__] = objects[i].id

        if len(columns) == 2:
            self.database.sql.delete(unity_table, data)
        elif len(columns) == 1:
            self.database.sql.update_where(unity_table, none_data, where)

    def delete(self):
        """
        Delete database entry and make further use of this instance impossible
        """
        if self.id is not None:
            self.database.sql.delete(
                self.__TableName__,
                {self.__IDField__: self.id})
        self.__dict__ = dict()


class Book(TableEntityWithID):
    """
    Single library item. Needs CatalogueDB() connection
    """
    __TableName__ = "books"
    __IDField__ = "id"

    def __init__(self, db, id=None):
        TableEntityWithID.__init__(self, db, id)
        self._simple_attrs("name",
                           "price",
                           "publisher",
                           "year",
                           "in_type",
                           "in_comment",
                           "out_type",
                           "out_comment",
                           "thumbnail_id",
                           "in_comment",
                           "annotation")
        self._simple_date_attrs("in_date",
                                "out_date",
                                "last_edit")

    @property
    def isbn(self):
        if self._data:
            s = ISBN(self._data["isbn"])
            return s.pretty

    @isbn.setter
    def isbn(self, value):
        if (not self._new and ISBN(self.isbn) != ISBN(value)) or (self._new):
            if ISBN(value).valid:
                self._changes["isbn_user"] = value
                self._saved = False
            else:
                raise ValueError("ISBN is not valid: %s" % value)


class Author(TableEntityWithID):
    __TableName__ = "authors"
    __IDField__ = "id"

    def __init__(self, db, id=None):
        TableEntityWithID.__init__(self, db, id)
        self._simple_attrs("name")


class Group(TableEntityWithID):
    __TableName__ = "groups"
    __IDField__ = "id"

    def __init__(self, db, id=None):
        TableEntityWithID.__init__(self, db, id)
        self._simple_attrs("name")


class User(TableEntityWithID):
    __TableName__ = "users"
    __IDField__ = "id"

    def __init__(self, db, id=None):
        TableEntityWithID.__init__(self, db, id)
        self._simple_attrs(
            "name",
            "hash",
            "fullname")
        self._simple_date_attrs(
            "created_on",
            "expires_on")

    def __password_set(self, password):
        """Set new password. Write-only property"""
        self.hash = PassHash.get(password)
    password = property(fset=__password_set)

    def check(self, password):
        """Validate password against saved hash"""
        return PassHash.check(password, self.hash)

    @property
    def expired(self):
        return bool(self.expires_on) and (datetime.now() > self.expires_on)


class Series(TableEntityWithID):
    __TableName__ = "series"
    __IDField__ = "id"

    def __init__(self, db, id=None):
        TableEntityWithID.__init__(self, db, id)
        self._simple_attrs("type",
                           "name",
                           "number_books")

    def position(self, book):
        """Return position of Book object in the Series"""
        if type(book) is Book:
            question = book.id
        else:
            question = book
        search = self.database.sql.select(
            "book_series",
            where={"series_id": self.id, "book_id": question},
            what="book_number")
        result = search.fetchone()
        if result:
            position = result[0]
            return position


class AuthorRating(TableEntityWithID):
    __TableName__ = "author_ratings"
    __IDField__ = "id"

    def __init__(self, db, id=None):
        TableEntityWithID.__init__(self, db, id)
        self._simple_attrs("author_id",
                           "rated_by",
                           "value",
                           "comment")
        self._simple_date_attrs("date")


class BookReview(TableEntityWithID):
    __TableName__ = "book_reviews"
    __IDField__ = "id"

    def __init__(self, db, id=None):
        TableEntityWithID.__init__(self, db, id)
        self._simple_attrs("book_id",
                           "reviewed_by",
                           "review",
                           "rating")
        self._simple_date_attrs("date")


class BookFile(TableEntityWithID):
    __TableName__ = "files"
    __IDField__ = "id"

    def __init__(self, db, id=None):
        TableEntityWithID.__init__(self, db, id)
        self._simple_attrs("name",
                           "type")


class Tag(TableEntityWithID):
    __TableName__ = "tags"
    __IDField__ = "id"

    def __init__(self, db, id=None):
        TableEntityWithID.__init__(self, db, id)
        self._simple_attrs("name")


class Thumbnail(TableEntityWithID):
    __TableName__ = "thumbs"
    __IDField__ = "id"
    __MAXSIZE__ = (400, 550)  # todo: maybe smaller?

    def __init__(self, db, id=None):
        TableEntityWithID.__init__(self, db, id)
        self._simple_attrs("url")
        self._simple_date_attrs("last_edit")

    @property
    def image(self):
        if self._data:
            return self._data["image"]

    @image.setter
    def image(self, data):
        if type(data) is bytes:
            img = Image.open(io.BytesIO(data))
        elif hasattr(data, "read") \
        and hasattr(data, "readable") \
        and hasattr(data, "tell") \
        and data.readable():
            img = Image.open(data)
        else:
            raise TypeError("image has to be bytestring or file-like object")

        img.thumbnail(self.__MAXSIZE__)
        pic = io.BytesIO()
        img.save(pic, format="jpeg")
        del img
        pic.seek(0)
        self._changes["image"] = pic.read()
        del pic
        self._saved = False


class Barcode(TableEntityWithID):
    __TableName__ = "barcode_queue"
    __IDField__ = "id"

    def __init__(self, db, id=None):
        TableEntityWithID.__init__(self, db, id)
        self._simple_attrs("title")
        self._simple_date_attrs("date")

    @property
    def isbn(self):
        if self._data:
            return self._data["isbn"]

    @isbn.setter
    def isbn(self, value):
        input = ISBN(value)
        if (not self._new and self._data["isbn"] != input.number) or (self._new):
            if input.valid:
                self._changes["isbn"] = input.number
                self._saved = False
            else:
                raise ValueError("ISBN is not valid: %s" % value)


class ISBN(object):
    """
    Class for handling ISBN numbers

    Properties:
        value:    String. Initial value
        number:   String. Only numeric characters and X
        valid:    Boolean. Checks if ISBN is valid
        pretty:   String. Formatted for readability
    """
    def __init__(self, text):
        self.value = text

    def __eq__(self, other):
        try:
            return (self.number == other.number) \
                and (type(self) == type(other))
        except Exception:
            return False

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newtext):
        self._value = str(newtext)
        self._number = None
        self._valid = None
        self._pretty = None

    @property
    def number(self):
        if self._number is None:
            new_number = re.sub("[^\dxX]", "", self.value).upper()
            if new_number:
                self._number = new_number
        return self._number

    @property
    def valid(self):
        if self._valid is None:
            length = len(str(self.number))
            if length == 10 or length == 13:
                self._valid = True
            elif not self.value:
                self._valid = True
            else:
                self._valid = False

            if self._valid and self.number:
                left, right = self.number[:-1], self.number[-1]
                try:
                    int(left)
                except ValueError:
                    self._valid = False
                if self._valid:
                    try:
                        int(right)
                    except ValueError:
                        self._valid = right == "X"
        return self._valid

    @property
    def pretty(self):
        if not self._pretty:
            accum = ""
            if self.valid:
                tick = 0
                for i in str(self.number):
                    accum += i
                    tick += 1
                    if tick % 3 == 0:
                        accum += "-"
            self._pretty = accum
        return self._pretty
