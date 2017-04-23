"""
HomeLibraryCatalog main code module
"""

import sqlite3
import os
import json
import re
import sys
import webbrowser
from threading import Timer
from datetime import datetime, timedelta
from bottle import Bottle, TEMPLATE_PATH, request, abort, response, \
                   template, redirect, static_file
from hlc.items import NoneMocker, Author, User, Thumbnail, ISBN, Group
from hlc.db import CatalogueDB, DBKeyValueStorage
from hlc.util import LinCrypt, timestamp, debug, random_str, message


class validate(object):
    """
    A collection of functions for validating user input

    All methods return 2-tuple: boolean status of validation and preprocessed
    value after validation
    """

    @staticmethod
    def nonempty(text):
        valid = bool(text)
        try:
            text = str(text)
        except Exception:
            valid = False
        if valid:
            text = re.sub("^\s+|\s+$", "", text)
            valid = len(text) > 0
        return valid, text

    @staticmethod
    def date(text):
        """DD.MM.YYYY format"""
        text = validate.nonempty(text)[1]
        valid = False
        try:
            delimiter = re.sub("\d", "", text)[0]
            date_seq = text.split(delimiter)
            date_seq = [int(x) for x in date_seq]
        except Exception as e:
            date_seq = list()
        if len(date_seq) == 3:
            try:
                valid = validate.year(date_seq[-1])[0]
                text = datetime(date_seq[-1],
                                date_seq[-2],
                                date_seq[-3],
                                12,
                                0)
            except Exception as e:
                valid = False
        return valid, text

    @staticmethod
    def year(text):
        valid, text = validate.nonempty(text)
        if valid:
            valid, text = validate.positive(text)
        if valid:
            try:
                text = int(text)
            except Exception:
                valid = False
        if valid:
            valid = text >= 1900 and text <= 2100
        return valid, text

    @staticmethod
    def positive(text):
        valid, text = validate.nonempty(text)
        text = text.replace(",", ".")
        if valid:
            try:
                text = float(text)
            except Exception:
                valid = False
        if valid:
            valid = text > 0
        return valid, text

    @staticmethod
    def isbn(text):
        try:
            valid = ISBN(text).valid
        except Exception:
            valid = False
        return valid, text


class WebUI(object):
    """
    Interactive user interface. Starts its own web server, saves user input to
    database.

    Methods:
        start(browser=False, *a, **kw)
            Start web server, open starting page in web browser. Extra arguments
            are passed to bottle.run() method
        close()
            Stop web server, close database connection, exit WebUI application
        booksearch(search, sort_keys=None)
            Full text search for books
        adduser(username, password)
            Create new user

    Properties:
        db
            CatalogueDB() object. Database interaction layer
        app
            Bottle() object. Main (and the only) web application
        session
            SessionManager() object. Stores sessions for normal users
        info
            Dictionary with some basic stats

    Access control wrappers:
        __uac_user

    Internal functions:
        __create_routes(routes, wrapper)
        __update_info()

    Route callback functions:
        _clbk_hello
        _clbk_login
        _clbk_logout
        _clbk_thumb
        _clbk_allbooks
    """
    def __init__(self, sqlite_file):
        self.__db = CatalogueDB(sqlite_file)
        self.__persistent_cfg = DBKeyValueStorage(
            self.db.cursor.connection,
            "app_config",
            "option",
            "value"
        )
        self.__clean_init()
        self.__app = Bottle()
        self.__session_manager = SessionManager()
        self.__update_info()
        self.__datadir = os.path.dirname(os.path.abspath(sqlite_file))

        routes_for_all = (
            ("/login", self._clbk_login, ["GET", "POST"]),
            ("/logout", self._clbk_logout),
            ("/table/<table>", self._clbk_table),
            ("/books", self._clbk_allbooks),
            ("/add", self.__clbk_editbook, ["GET", "POST"]),
            ("/static/<filename:path>", self._clbk_static),
            ("/ajax/suggest", self._clbk_suggestions))
        authorized_routes = (
            ("/", self._clbk_hello),
            ("/quit", self.close),
            ("/thumbs/<hexid>", self._clbk_thumb))
        self.__create_routes(routes_for_all)
        self.__create_routes(authorized_routes, self.__uac_user)

    def _clbk_suggestions(self):
        params = request.query.decode()
        line, field = params.get("q"), params.get("f")
        suggestions = self.suggest(field, line)
        return json.dumps({field: suggestions})
        
    def __clean_init(self):
        """
        First start. Initialize some database entries
        """
        options = self.__persistent_cfg
        if not options.get("init_date"):
            # create Group admin
            admins = Group(self.db)
            admins.name = "admin"
            admins.save()
            
            # create Group user
            users = Group(self.db)
            users.name = "user"
            users.save()
            
            # create User admin_XXX with random password
            root = User(self.db)
            credentials = (
                "admin_" + random_str(2,4).upper(),
                random_str(6,8)
            )
            root.name, root.password = credentials
            root.expires_on = datetime.now() + timedelta(days=1)
            root.save()
            
            # show random password to user
            msg = "Created initial administrative account:\n Login: %s\n Password: %s"
            message(msg % credentials)  # todo: show in web interface
            
            # save application state (first run = passed)
            options["init_date"] = timestamp()

    def suggest(self, field, input):
        """
        Return suggestions based on user input
        """
        translate = {
            "title": ("books", "name")
        }  # form field: (db table, db column)
        # todo: support more fields

        result = list()
        if field in translate:
            table, column = translate[field]
            result = self.db.getsuggestions(str(input), table, column)
        return result

    def __clbk_editbook(self, id=None):
        """
        Add/edit books
        """  # todo: unfinished
        if request.method == "GET":
            if id:
                book = self.db.getbook(id=id)
            else:
                book = NoneMocker()
            if book.saved:
                title = "Редактировать книгу"
                authors = book.getconnected(Author)
            else:
                title = "Новая книга"
                authors = (NoneMocker(),)
            return template("book_edit",
                book=book,
                authors=authors,
                title=title,
                info=self.info)
        else:
            form = request.forms.decode()
            book = self.db.getbook()

            # 3-tuples: attr name, input name, validator function
            inputs = (("name", "title", validate.nonempty),
                      ("isbn", "isbn", validate.isbn),
                      ("publisher", "publisher", validate.nonempty),
                      ("year", "year", validate.year),
                      ("price", "price", validate.positive),
                      ("in_date", "in_date", validate.date),
                      ("in_type", "in_type", validate.nonempty),
                      ("in_comment", "in_comment", validate.nonempty))

            for attr, input, func in inputs:
                valid, value = func(form.get(input))
                if valid:
                    setattr(book, attr, value)

            try:
                book.save()
            except sqlite3.IntegrityError as e:
                raise e  # todo: handle error

            for name in form.getall("author"):
                name = name.strip()
                if name:
                    author = self.db.getauthor(name)
                    author.save()
                    try:
                        book.connect(author)
                    except sqlite3.IntegrityError as e:
                        raise e  # todo: handle error
            redirect("/table/books")  # todo: replace with book page

    def booksearch(self, search, sort_keys=None):
        """
        Search for string in most important book properties

        Returns number of books matching the query and generator object
        yielding Book instances for books matching the search string

        Arguments:
            search
                String, user input. Search query. Accepts "*" as wildcard
            sort_keys
                Tuple of sort keys. Possible values are "in_date", "year",
                "title", "author". Raises sqlite3.OperationalError if invalid
                sort key is supplied
        """
        # sqlite's fts3,fts4,fts5 are much more superior, but Python's default
        # build of this library does not support those extensions

        wildcard = "*"  # single char

        search = re.sub("\s+", " ", search).strip()
        search = re.sub("[^\d\w %s]" % wildcard, "", search).lower()
        words = search.split(" ")
        for i in range(len(words)):
            new_word = words[i]
            if new_word[0] != wildcard:
                new_word = " " + new_word
            if words[i][-1] != wildcard:
                new_word = new_word + " "
            words[i] = new_word.replace(wildcard, "")
        where_clause = " AND ".join("instr(info, ?)>0" for w in words)

        if not sort_keys:
            sort_keys = ("in_date",)
        order_clause = ", ".join(sort_keys)

        query = "SELECT DISTINCT id FROM search_books WHERE %s ORDER BY %s" % (
            where_clause, order_clause)

        count = 0
        books_generator = ()
        if words:
            cur = self.db.cursor
            cur.execute(query, tuple(words))
            results = cur.fetchall()
            count = len(results)
            books_generator = (self.db.getbook(row["id"]) for row in results)
        return count, books_generator

    def adduser(self, username, password):
        """
        Create new WebUI user

        Returns User() instance
        Raises sqlite3.IntegrityError if username is already taken
        """
        user = User(self.db)
        user.name = username
        user.password = password
        user.save()
        return user

    def _clbk_allbooks(self):
        search = self.db.sql.select("books", what="id")
        books = (self.db.getbook(row["id"]) for row in search.fetchall())
        return template("manybooks", books=books, info=self.info)

    def __del__(self):
        self.close()

    def __create_routes(self, routes, wrapper=None):
        """
        Create multiple routes at once. Decorate callback functions in wrapper
        if needed

        Arguments:
            routes: List of tuples, each containing information about a single
                    route: (url, callback, method=GET). Raises ValueError if
                    length of any route tuple is not 2 or 3
            wrapper: Optional. Decorator function applied to all callback
                    functions, for example: checking user access level
        """
        for route in routes:
            url, func = route[:2]
            if wrapper:
                func = wrapper(func)
            if len(route) == 3:
                method = route[2]
            elif len(route) == 2:
                method = "GET"
            else:
                raise ValueError("Invalid route tuple of length=%s" % len(route))
            self.app.route(url, method=method, callback=func)

    def __uac_user(self, func):
        """Wrapper for callback functions. Checks authorization for normal users"""
        def newfunc(*a, **ka):
            cookie = request.get_cookie("auth", secret=self.__cookie_secret)
            auth = self.session.valid(cookie)  # todo: add timestamp check, delete old cookies
            if auth:
                return func(*a, **ka)
            else:
                abort(403, "You do not have permission to access this page")
                # replace with proper redirect to login page
        return newfunc

    def __update_info(self):
        i = self.__info = dict()
        i["books_count"] = len(self.db.sql.select("books").fetchall())
        i["copyright"] = "2016-%s" % datetime.now().year
        i["date"] = datetime.now().strftime("%d.%m.%Y")

    @property
    def db(self):
        """CatalogueDB object. Used for storing persistent data"""
        return self.__db

    @property
    def app(self):
        """Bottle application"""
        return self.__app

    @property
    def session(self):
        """SessionManager() object"""
        return self.__session_manager

    @property
    def info(self):
        """Access the dictionary with some basic stats and other information"""
        return self.__info

    def start(self, config, browser=False, *a, **kw):
        """Start WebUI"""
        self.__scramble_key = int(config.id_key)
        self.__cookie_secret = str(config.cookie_key)
        self.__static_location = str(config.static_dir)
        self.__stpl_location = str(config.templates_dir)

        TEMPLATE_PATH.insert(
            0, os.path.join(self.__datadir, self.__stpl_location)
        )

        if browser:
            if len(a) > 2:
                host = a[2]
            elif "host" in kw:
                host = kw["host"]
            else:
                host = "127.0.0.1"

            if len(a) > 3:
                port = a[3]
            elif "port" in kw:
                port = kw["port"]
            else:
                port = "8080"

            url = "http://%s:%s" % (host, port)
            Timer(1.25, lambda: webbrowser.open(url)).start()  # todo: replace webbrowser.open() with proper handler
        self.app.run(*a, **kw)

    def close(self):
        """Stop WebUI: stop server, close database"""
        self.app.close()
        self.db.close()
        sys.stderr.close()  # not ideal, but I don't know any better

    def _clbk_thumb(self, hexid):
        """Show thumbnail based on encrypted `hexid`"""
        picture = None
        try:
            id = LinCrypt(self.__scramble_key).decode(hexid)
            picture = Thumbnail(self.db, id).image
        except ValueError:
            abort(404, "Invalid thumnail ID: %s" % hexid)
        response.content_type = "image/jpeg"
        return picture

    def _clbk_hello(self):
        return "Hello World!"

    def _clbk_login(self):  # todo: stub
        form = request.forms.decode()
        user = form.get("user")
        password = form.get("password")
        if user and password:
            debug("User: %s\nPassword: %s" % (user, password))
            row = self.db.sql.select("users", {"name": user}).fetchone()
            if row:
                saved_user = User(self.db, row["id"])
                if saved_user.check(password):
                    cookie = (saved_user.id, timestamp())
                    self.session.new(cookie)
                    response.set_cookie(
                        "auth",
                        json.dumps(cookie),
                        secret=self.__cookie_secret)
                    redirect("/")
            return "Incorrect username or password: %s, %s" % (user, password)  # todo: replace with template
        else:
            return template("login_password", info=self.info)

    def _clbk_logout(self):  # todo: stub
        cookie = request.get_cookie("auth", secret=self.__cookie_secret)
        self.session.delete(cookie)
        response.delete_cookie("auth")
        return "You are now logged out"

    def _clbk_static(self, filename):
        return static_file(filename, root=os.path.join(self.__datadir, self.__static_location))

    def _clbk_table(self, table):
        try:
            return template("table",
                cursor=self.db.sql.select(table),
                title=table,
                info=self.info)
        except sqlite3.OperationalError:
            abort(404, "Table `%s` not found in %s" % (table, self.db.filename))


class SessionManager(object):
    """Manage sessions for WebUI. Draft API implementation"""  # todo
    def __init__(self):
        self.__sessions = set()  # set of tuples (user_id, unix_timestamp)

    def __call__(self, cookie):
        """Turn JSON cookie into a tuple"""
        if cookie:
            if type(cookie) is str:
                cookie = json.loads(cookie)
                return tuple(cookie)
            else:
                raise ValueError(
                    "expected string, but got %s" %
                    type(cookie))

    def new(self, item):
        """Save new session represented by tuple"""
        if type(item) is tuple:
            self.__sessions.add(item)
        else:
            raise ValueError("expected tuple, but got %s" % type(item))

    def delete(self, cookie):
        """Remove stored session represented by JSON string"""
        if self.valid(cookie):
            self.__sessions.remove(self(cookie))  # todo: stub

    def valid(self, cookie):
        """Check if a cookie JSON string represents a valid session"""
        try:
            return self(cookie) in self.__sessions
        except (TypeError, ValueError):
            return False
