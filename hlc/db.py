"""
Manage database interaction
"""

import sqlite3
import os
import re
from hlc.items import ISBN, Author, Book, Series, Tag
from hlc.util import lowercase, alphanumeric, debug, timestamp, printf_replacement
from hashlib import sha224

if sqlite3.sqlite_version_info < (3, 8, 11):
    print("\n".join([
        "WARNING! YOU ARE USING A VERY OLD VERSION OF SQLITE!",
        "It has been released in 2015 or earlier. Some database features may not work",
        "Please consider updating at least to 3.8.11"]))


class FSKeyFileStorage(object):
    """
    Dictionary-like object for storing key:file pairs in file system

    Methods:
        get, pop, __contains__, __getitem__, __setitem__
            Mimic behavior of dict() object
        open(key, *a, **kw)
            Execute Python's open function with self[key] as filename
            and *a, **kw as arguments
    """
    __readme = "README"

    def __init__(self, folder_name, max_filesize=None):
        """
        Arguments:
            folder_name
                Top directory containing stored files
        """
        try:
            os.makedirs(folder_name, exist_ok=True)
        except FileExistsError as e:
            pass
        self.__dir = os.path.abspath(folder_name)
        self.__add_readme(self.__readme)
        if max_filesize is None:
            self.__max_size = None
        else:
            self.__max_size = int(max_filesize)

    def __add_readme(self, readme_file):
        text = "THIS FOLDER IS USED BY AN APPLICATION FOR STORING FILES\n"
        text += "THIS IS NOT A TEMP FOLDER\n"
        text += "DO NOT DELETE OR MODIFY ANY FILES MANUALLY\n"
        readme_file = os.path.join(self.__dir, readme_file)
        if not os.path.isfile(readme_file):
            with open(readme_file, "w", encoding="utf-8") as f:
                f.write(text)

    def __hash(self, key):
        """Get hash string from a key"""
        key = str(key).encode()
        hash = sha224(key).hexdigest()
        return hash

    def __path(self, key):
        """Get file path from a key"""
        hash = self.__hash(key)
        elements = [hash[:2], hash[2:5], hash[5:]]
        return os.path.join(self.__dir, *elements)

    def __contains__(self, key):
        """
        Handle python `in` operator. Returns True if a file exists that
        corresponds to key
        """
        return os.path.isfile(self.__path(key))

    def __getitem__(self, key):
        """
        Return path of stored file corresponding to key

        Raises KeyError if key is not in self
        """
        if key in self:
            return self.__path(key)
        else:
            raise KeyError(key)

    def get(self, key, default=None):
        """
        Return self[key] or default value if key is not in self
        """
        try:
            return self[key]
        except KeyError:
            return default

    def open(self, key, *a, **kw):
        """
        Return file handler object, pass *a and **kw to Python open() function
        """
        return open(self[key], *a, **kw)

    def __setitem__(self, key, value):
        """
        Store a file corresponding to key. Value has to be a file-like object
        """
        if value.readable() and value.seekable():
            path = self.__path(key)
            dir = os.path.dirname(path)
            try:
                mode = value.mode.lower()
                mode = re.sub("[wrax]", "w", mode)
            except AttributeError:
                mode = "wb"
            try:
                enc = value.encoding
            except AttributeError:
                enc = None

            try:
                os.makedirs(dir, exist_ok=True)
            except FileExistsError as e:
                pass
            with open(path, mode, encoding=enc) as fp:
                offset = value.tell()
                chunk_size = 2**16
                size = 0
                while True:
                    buf = value.read(chunk_size)
                    size += len(buf)
                    if self.__max_size and size > self.__max_size:
                        fp.close()
                        del self[key]
                        raise ValueError(
                            "file size exceeds %s bytes" % self.__max_size)
                        break
                    if buf:
                        fp.write(buf)
                    else:
                        break
                value.seek(offset)
        else:
            raise ValueError("object has to be readable and seekable")

    def __delitem__(self, key):
        value = self[key]
        if os.path.isfile(value):
            os.remove(value)
        cur = value
        del_parent = True
        while del_parent:
            cur = os.path.dirname(cur)
            try:
                os.rmdir(cur)
            except (OSError, FileNotFoundError) as e:
                del_parent = False

    def pop(self, key, default=KeyError):
        if key in self:
            value = self[key]
            del self[key]
            return value
        elif default == KeyError:
            raise KeyError(key)
        else:
            return default


class SQLBaseWithEscaping(object):
    """
    Base class for supporting escaped field names and making SQL queries
    """
    __escape_chars = ('"', '"')

    @property
    def esc_chars(self):
        """Strings used to escape table/field names"""
        return self.__escape_chars

    @esc_chars.setter
    def esc_chars(self, chars):
        chars = [str(c) for c in chars[:2]]
        self.__escape_chars = tuple(chars)

    def _escape_identifier(self, text, esc_chars=None):
        """Return escaped database identifier (field, table)"""
        # do not escape some special cases
        special_cases = set(("*",))

        if esc_chars is None:
            esc_chars = self.__escape_chars

        text = str(text)
        if set(text).intersection(set(esc_chars)) or text[-1]=="\\":
            # todo: escape vulnerable chars
            raise ValueError("injection vulnerability: [\%s] are not allowed" % ("".join(esc_chars), ))

        if text not in special_cases:
            return text.join(esc_chars)
        else:
            return text

    def _escape_seq(self, identifiers, esc_chars=None):
        """Apply _escape_identifier() method to sequence of strings"""
        return tuple(map(
            self._escape_identifier,
            identifiers,
            (esc_chars for i in iter(int, 1))))

    def generic(self, connection, query, fields=(), params=(), commit=False):
        """
        Generic SQL query with proper escaping
        For internal use

        Arguments:
            connection
                DB API connection
            query
                SQL query with two kinds of placeholders:
                %s for trusted input (field names, table names)
                ?  for untrusted input. Works only where values are expected
            fields
                Tuple of strings with trusted inputs
                Will be applied like: query % fields
            params
                Tuple of strings with untrusted inputs. Will be passed to the
                connection.cursor().execute() method
            commit
                Boolean. If True connection.commit() will be called after
                executing the query
        """
        if fields:
            fields = tuple(map(self._escape_identifier, fields))
            query = query % fields
        cur = connection.cursor()
        try:
            cur.execute(query, params)
        except Exception as e:
            connection.rollback()
            raise e
        if commit:
            connection.commit()
        return cur


class DBKeyValueStorage(SQLBaseWithEscaping):
    """
    Dictionary-like object for storing key:value pairs in database table

    Methods:
        get, pop, __contains__, __getitem__, __setitem__
            Mimic behavior of dict() object
        _escape_identifier(text, esc_chars=None)
            Returns escaped database identifier (field name, table name) with
            brackets or quotes specified in self.esc_chars or in esc_chars
            if passed as an argument

    Properties:
        esc_chars
            Two character tuple (begin, end) used to escape table names and
            column names in SQL queries. Double quotes by default.
    """

    def __init__(self, connection, table, key_field, value_field):
        """
        Arguments:
            connection
                Database connection supporting Python DB API (PEP 249)
            table
                Name of the table which stores key:value pairs
            key_field, value_field
                Fields storing keys and values
        """
        self.__db = connection
        self.__table = str(table)
        self.__keyfield = str(key_field)
        self.__valfield = str(value_field)

    def __contains__(self, key):
        """
        Handle python `in` operator. Returns True if key is found in key_field
        """
        try:
            self[key]
            return True
        except KeyError:
            return False

    def __getitem__(self, key):
        """
        Return self[key] value

        Raises:
            KeyError if key is not in self
            LookupError table contains multiple entries with the same key
        """
        args = (self.__valfield, self.__table, self.__keyfield)
        query = "SELECT %s FROM %s WHERE %s=?"
        search = self.generic(self.__db, query, args, (key,))
        result = search.fetchone()
        second = search.fetchone()
        if result and not second:
            return result[0]
        elif not result and not second:
            raise KeyError(key)
        else:
            raise LookupError("multiple values with key: %s" % key)

    def get(self, key, default=None):
        """
        Return self[key] or default value if key is not in self
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key, value):
        """
        Set self[key] value
        """
        if key in self:
            query = "UPDATE %s SET %s=? WHERE %s=?"
        else:
            query = "INSERT INTO %s (%s,%s) VALUES (?,?)"
        args = (self.__table, self.__valfield, self.__keyfield)
        params = (value, key)
        self.generic(self.__db, query, args, params, commit=True)

    def __delitem__(self, key):
        """
        Delete self[key]
        """
        self[key]  # raises KeyError if needed
        query = "DELETE FROM %s WHERE %s=?"
        args = (self.__table, self.__keyfield)
        params = (key,)
        self.generic(self.__db, query, args, params, commit=True)

    def pop(self, key, default=KeyError):
        """
        Return self[key] and delete this entry from storage.
        If key is not found in self, default value is returned.
        If no default value is specified, KeyError is raised
        """
        if key in self:
            value = self[key]
            del self[key]
            return value
        elif default == KeyError:
            raise KeyError(key)
        else:
            return default


class SQL(SQLBaseWithEscaping):
    """
    Perform common SQL queries on database connection providing Python DB API

    Methods:
        select
        delete
        insert
        update_where
        table2text
    """
    def __init__(self, dbapi_connection):
        """
        dbapi_connection
            Connection object providing Python DB API (PEP 249)
        """
        self.__dbapi = dbapi_connection

    def select(self, table, where=None, what="*", order=None):
        """
        Run SQL SELECT operation

        Arguments
            table:  String. The name of the table to be updated
            where:  Dictionary. {field=requirement} pairs
            what:   String or sequence of strings. Optional. Field names
                    to be selected.
            order:  String or sequence of string. Optional. ORDER commands

        Returns cursor object
        """
        fields = list()
        if type(what) is str:
            fields.append(what)
        else:
            fields += list(what)

        query_template = 'SELECT %s FROM %s' % (
            ", ".join(self._escape_seq(fields)),
            self._escape_identifier(table))

        if where:
            query_template += " WHERE "
            where_clause = " AND ".join(
                tuple(str(x) + "=?" for x in self._escape_seq(where.keys())))
            query_template += where_clause

        order_cmds = list()
        if order:
            if type(order) is str:
                order_cmds.append(order)
            else:
                order_cmds = list(order)
        order_clause = str()
        if order_cmds:
            order_clause = " ORDER BY "
            order_clause += ", ".join(order_cmds)
        query_template += order_clause

        cursor = self.__dbapi.cursor()
        cursor.execute(query_template,
                       list(where.values()) if where else tuple())
        return cursor

    def delete(self, table, where):
        """
        Run SQL DELETE operation

        Arguments:
            table:  String. The name of the table to be updated
            where:  Dictionary. {field=requirement} pairs

        Returns number of affected rows
        """
        query_template = 'DELETE FROM %s' % self._escape_identifier(table)

        if where:
            query_template += " WHERE "
            where_clause = " AND ".join(
                tuple(str(x) + "=?" for x in self._escape_seq(where.keys())))
            query_template += where_clause

        cursor = self.__dbapi.cursor()
        try:
            cursor.execute(query_template,
                           list(where.values()) if where else tuple())
        except Exception as e:
            cursor.connection.rollback()
            raise e
        cursor.connection.commit()
        return cursor.rowcount

    def insert(self, table, data):
        """
        Run SQL INSERT operation

        Arguments:
            table:  String. The name of the table to be updated
            data:   Dictionary. {field=new value} pairs

        Returns rowid of the inserted row
        """
        query_template = 'INSERT INTO %s #FIELDS# VALUES #VALUES#' % \
            self._escape_identifier(table)
        query_template = query_template.replace("#FIELDS#",
            "(" + ",".join(tuple('%s' for x in range(len(data)))) + ")")
        query_template = query_template.replace("#VALUES#",
            "(" + ",".join(tuple("?" for x in range(len(data)))) + ")")
        cursor = self.__dbapi.cursor()
        try:
            cursor.execute(query_template % self._escape_seq(data.keys()),
                           list(data.values()))
        except Exception as e:
            cursor.connection.rollback()
            raise e
        cursor.connection.commit()
        return cursor.lastrowid

    def update_where(self, table, data, where):
        """
        Run SQL UPDATE operation

        Arguments:
            table:  String. The name of the table to be updated
            data:   Dictionary. {field=new value} pairs
            where:  Dictionary. {field=requirement} pairs

        Returns number of affected rows
        """
        query_template = 'UPDATE %s SET #VALUES#' % \
            self._escape_identifier(table)

        if where:
            query_template += " WHERE "
            where_clause = " AND ".join(
                tuple(str(x) + "=?" for x in self._escape_seq(where.keys())))
            query_template += where_clause

        query_template = query_template.replace(
                 "#VALUES#",
                 ",".join(tuple('%s=?' for x in range(len(data)))))

        cursor = self.__dbapi.cursor()
        try:
            cursor.execute(query_template % self._escape_seq(data.keys()),
                  list(data.values()) + (list(where.values()) if where else list()))
        except Exception as e:
            cursor.connection.rollback()
            raise e
        cursor.connection.commit()
        return cursor.rowcount

    @staticmethod
    def iterate(cursor, limit=-1, arraysize=1000):
        """Use this generator to efficiently iterate over cursor results"""
        # todo: find out if OFFSET is possible without altering query
        row_number = 0
        exit = False
        while not exit:
            chunk = cursor.fetchmany(arraysize)
            if not chunk:
                break
            for row in chunk:
                if limit >= 0 and row_number >= limit:
                    exit = True
                    break
                row_number += 1
                yield row

    def table2text(self, table):
        """
        Return SQL table represented as string. Useful for debugging purposes

        Arguments:
            table: String. Table name
        """
        select = self.select(table)
        text = str()
        for row in self.iterate(select):
            if len(text) == 0:
                text += str(row.keys())
            text += "\n" + str(tuple(row))
        return text


class SQLiteDB(object):
    """
    SQLite database with some extra methods and properties

    Methods:
        close()
            Close database connection

    Properties:
        connection
            Get DB API connection
        sql
            SQL() object. Contains methods for performing most popular queries
        filename
            Database file name with full path
    """
    def __init__(self, filename):
        sqlite3.enable_callback_tracebacks(True)  # debug
        self._connection = sqlite3.connect(filename)
        self._connection.row_factory = sqlite3.Row

        self._connection.create_function("clean_isbn", 1,
            lambda x: ISBN(x).number)
        self._connection.create_function("lower", 1, lowercase)
        self._connection.create_function("printf", -1, printf_replacement)
        self._connection.create_function("simplify", 1,
            lambda x: lowercase(alphanumeric(x)))
        # self._connection.create_function("timestamp", 0, timestamp)

        self._dbfile = os.path.abspath(filename)
        self._sql = SQL(self._connection)

    def __eq__(self, other):
        try:
            return (self.filename == other.filename) \
                and (type(self) == type(other))
        except Exception:
            return False

    def __del__(self):
        self.close()

    @property
    def connection(self):
        return self._connection

    @property
    def sql(self):
        return self._sql

    @property
    def filename(self):
        return self._dbfile

    def close(self):
        try:
            self._connection.close()
        except AttributeError:
            pass


class CatalogueDB(SQLiteDB):
    """
    Class for the home library database interaction

    Methods:
        getbook(id=None, isbn=None)
            Fetch book entry from the database (by ISBN or by ID)
            Returns new Book() object if no id or isbn is specified
        getauthor(name)
            Fetch Author object from database. If no author with this name
            exists, new Author object is created
        create_db(db_filname)
            Create new SQLite database. Dates and times are stored
            in Unix epoch format
    """
    def __init__(self, filename):
        new = not os.path.isfile(filename)

        SQLiteDB.__init__(self, filename)
        if new:
            self.create_db(filename)

    def getsuggestions(self, beginning, table, field, count=10):
        """
        Get suggestions
        """
        suggestions = list()
        if bool(beginning.strip()):
            query = """
                SELECT DISTINCT %s FROM %s
                WHERE simplify(%s) LIKE simplify(?) || "%%"
                ORDER BY %s
                """
            search = self.sql.generic(
                self.connection,
                query,
                (field, table, field, field),
                (beginning,))
            for result in self.sql.iterate(search, count):
                suggestions.append(result[0])
        return suggestions

    def get(self, cls, field, value, attr=None, simplify=False):
        """
        Get an instance of TableEntityWithID of class `cls` where field=value

        Returns:
            `cls` instance. If `value` was not found in `field`,
            returns new instance (not saved)
        """
        if attr is None: attr = field
        if value:
            if simplify:
                query = "SELECT %s FROM %s WHERE simplify(%s)=simplify(?)"
            else:
                query = "SELECT %s FROM %s WHERE %s=?"
            search = self.sql.generic(
                self.connection,
                query,
                (cls.__IDField__, cls.__TableName__, field),
                (value, ))
            result = search.fetchone()
            second = search.fetchone()
            if not result:
                inst = cls(self)
                setattr(inst, attr, value)
            elif result and not second:
                inst = cls(self, result[0])
            elif second:
                raise ValueError("%s contains more than one entry %s" %
                                 (self.filename, value))
            else:
                raise RuntimeError("Impossible branching")
        else:
            inst = None
        return inst

    def getauthor(self, name):
        """
        Get Author object from database

        Returns:
            Author() object. If `name` was not found in the database, returns
            new Author() object (not saved)
        """
        return self.get(Author, "name", name, simplify=True)

    def getseries(self, name):
        return self.get(Series, "name", name, simplify=True)

    def gettag(self, name):
        return self.get(Tag, "name", name, simplify=True)

    def getbook(self, id=None, isbn=None):
        """
        Get Book object from database

        Returns:
            Book() object: if the book with specified `id` or `isbn` was found
                           in the database
            New Book() object: if called without `id` or `isbn`
            None: if `id` or `isbn` wasn't found in the database
        """
        b = None
        if id is not None:
            search = self.sql.select(Book.__TableName__,
                    {Book.__IDField__: id}, Book.__IDField__)
            cur = search.fetchone()
            if cur:
                b = Book(self, cur[Book.__IDField__])
        elif isbn is not None:
            search = self.sql.select(Book.__TableName__,
                    {"isbn": ISBN(isbn).number}, Book.__IDField__)
            cur = search.fetchone()
            if cur:
                b = Book(self, cur[Book.__IDField__])
        if not b:
            b = Book(self)
        return b

    def create_db(self, db_filename):
        """Create new SQLite database file and all required tables"""
        # NOTE: increment CatalogueDB._schema_version and
        #       add SCHEMA_TRANSITIONS to db_transitions.py if changing schema
        new_table_queries = (
            """
            CREATE TABLE sessions (
                cookie text unique not null,
                session text)
            """,
            """
            CREATE TABLE users (
                id integer primary key,
                name text unique not null,
                fullname text,
                created_on integer not null default (cast(strftime('%s','now') as integer)),
                expires_on integer,
                hash text)
            """,
            """
            CREATE TABLE barcode_queue (
                id integer primary key,
                isbn text unique not null,
                user_id integer,
                date integer not null default (cast(strftime('%s','now') as integer)),
                title text,
                foreign key(user_id) references users(id) on delete cascade on update cascade
            )
            """,
            """
            CREATE TABLE groups (
                id integer primary key,
                name text unique not null)
            """,
            """
            CREATE TABLE user_groups(
                user_id integer not null,
                group_id integer not null,
                primary key (user_id, group_id),
                foreign key(user_id) references users(id) on delete cascade on update cascade,
                foreign key(group_id) references groups(id) on delete cascade on update cascade)
            """,
            """
            CREATE TABLE thumbs (
                id      integer primary key,
                url     text,
                image   blob,
                last_edit integer not null default (cast(strftime('%s','now') as integer)))
            """,
            """
            CREATE TABLE books (
                id          integer primary key,
                name        text not null,
                isbn_user   text,
                isbn        text unique,
                price       real check (price>=0),
                publisher   text,
                year        integer check (year>=1900 and year<=2100),
                annotation  text,
                in_date     integer,
                in_type     text,
                in_comment  text,
                out_date    integer,
                out_type    text,
                out_comment text,
                last_edit   integer not null default (cast(strftime('%s','now') as integer)),
                thumbnail_id integer,
                foreign key(thumbnail_id) references thumbs(id) on delete cascade on update cascade)
            """,
            """
            CREATE TRIGGER trg_thumbs_mtime BEFORE UPDATE ON thumbs
            BEGIN
                UPDATE thumbs SET last_edit = cast(strftime('%s','now') as integer) WHERE _rowid_ = NEW._rowid_;
            END
            """,
            """
            CREATE TRIGGER trg_book_mtime BEFORE UPDATE ON books
            BEGIN
                UPDATE books SET last_edit = cast(strftime('%s','now') as integer) WHERE _rowid_ = NEW._rowid_;
            END
            """,
            """
            CREATE TRIGGER trg_isbn_update AFTER UPDATE OF isbn_user ON books
            BEGIN
                UPDATE books SET isbn = clean_isbn(isbn_user) WHERE _rowid_ = NEW._rowid_;
            END
            """,
            """
            CREATE TRIGGER trg_clean_queue AFTER UPDATE OF isbn ON books
            BEGIN
                DELETE FROM barcode_queue WHERE isbn = NEW.isbn;
            END
            """,
            """
            CREATE TRIGGER trg_isbn_insert AFTER INSERT ON books
            BEGIN
                UPDATE books SET isbn = clean_isbn(isbn_user) WHERE _rowid_ = NEW._rowid_;
            END
            """,
            """
            CREATE TABLE authors (
                id      integer primary key,
                name    text unique not null)
            """,
            """
            CREATE TABLE series (
                id              integer primary key,
                type            text not null,
                name            text unique not null,
                number_books    integer check (number_books>0))
            """,
            """
            CREATE TABLE author_ratings (
                id          integer primary key,
                author_id   integer,
                date        integer not null default (cast(strftime('%s','now') as integer)),
                rated_by    integer not null,
                value       real,
                comment     text,
                foreign key(author_id) references authors(id) on delete cascade on update cascade,
                foreign key(rated_by) references users(id) on delete cascade on update cascade)
            """,
            """
            CREATE TABLE book_reviews (
                id          integer primary key,
                book_id     integer,
                date        integer not null default (cast(strftime('%s','now') as integer)),
                reviewed_by integer not null,
                review      text,
                rating      real,
                foreign key(book_id) references books(id) on delete cascade on update cascade,
                foreign key(reviewed_by) references users(id) on delete cascade on update cascade)
            """,
            """
            CREATE TABLE book_authors (
                book_id     integer not null,
                author_id   integer not null,
                primary key (book_id, author_id),
                foreign key(book_id) references books(id) on delete cascade on update cascade,
                foreign key(author_id) references authors(id) on delete cascade on update cascade)
            """,
            """
            CREATE TABLE book_series (
                book_id     integer not null,
                series_id   integer not null,
                book_number integer check (book_number>0),
                foreign key(book_id) references books(id) on delete cascade on update cascade,
                foreign key(series_id) references series(id) on delete cascade on update cascade,
                primary key (book_id, series_id),
                CONSTRAINT unq UNIQUE (series_id, book_number))
            """,
            """
            CREATE VIEW publishers AS
            SELECT DISTINCT publisher as name FROM books WHERE publisher NOT NULL
            """,
            """
            CREATE VIEW reviewers AS
            SELECT DISTINCT reviewed_by as name FROM book_reviews WHERE reviewed_by NOT NULL
            UNION
            SELECT DISTINCT rated_by as name FROM author_ratings WHERE rated_by NOT NULL
            """,
            """
            CREATE VIEW series_types AS
            SELECT DISTINCT type FROM series
            """,
            """
            CREATE VIEW search_books AS
            SELECT
                books.id as id,
                " " || simplify(printf("%s %s %s %s", books.name, books.isbn, authors.name, series.name)) || " " as info,
                books.in_date as in_date,
                books.year as year,
                books.name as title,
                authors.name as author
            FROM
            books
            LEFT JOIN book_authors ON book_authors.book_id = books.id
            LEFT JOIN authors ON book_authors.author_id = authors.id
            LEFT JOIN book_series ON book_series.book_id = books.id
            LEFT JOIN series ON series.id = book_series.series_id
            """,
            """
            CREATE TABLE app_config (
                option text unique not null,
                value text,
                help text,
                primary key(option))
            """,
            """
            CREATE TRIGGER trg_book_count1 AFTER INSERT ON books
            BEGIN
                UPDATE app_config
                SET value = (SELECT count(id) FROM books)
                WHERE option = "book_count";

                INSERT INTO app_config (option, value)
                SELECT "book_count", (SELECT count(id) FROM books)
                WHERE changes()=0;
            END
            """,
            """
            CREATE TRIGGER trg_book_count2 AFTER DELETE ON books
            BEGIN
                UPDATE app_config
                SET value = (SELECT count(id) FROM books)
                WHERE option = "book_count";

                INSERT INTO app_config (option, value)
                SELECT "book_count", (SELECT count(id) FROM books)
                WHERE changes()=0;
            END
            """,
            """
            CREATE TABLE files (
                id integer primary key,
                name text default "untitled",
                type text)
            """,
            """
            CREATE TABLE book_files (
                book_id integer not null,
                file_id integer not null,
                primary key (book_id, file_id),
                foreign key(book_id) references books(id) on delete cascade on update cascade,
                foreign key(file_id) references files(id) on delete cascade on update cascade)
            """,
            """
            CREATE TABLE tags (
                id      integer primary key,
                name    text unique not null)
            """,
            """
            CREATE TABLE book_tags (
                book_id     integer not null,
                tag_id   integer not null,
                primary key (book_id, tag_id),
                foreign key(book_id) references books(id) on delete cascade on update cascade,
                foreign key(tag_id) references tags(id) on delete cascade on update cascade)
            """)
        db = self.connection
        for query in new_table_queries:
            try:
                db.execute(query)
            except Exception as e:
                debug(query)
                db.rollback()
                raise e
        db.commit()
