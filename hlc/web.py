"""
HomeLibraryCatalog main code module
"""

import sqlite3
import os
import json
import re
import sys
import webbrowser
import urllib.parse
import urllib.request
from threading import Timer
from datetime import datetime, timedelta
from bottle import Bottle, TEMPLATE_PATH, request, abort, response, \
                   template, redirect, static_file
from hlc.items import NoneMocker, Author, User, Thumbnail, ISBN, Group, Series,\
                      BookFile, Tag, Barcode
from hlc.db import CatalogueDB, DBKeyValueStorage, FSKeyFileStorage
from hlc.util import LinCrypt, timestamp, debug, random_str, message, \
                     DynamicDict, ReadOnlyDict, parse_csv
from hlc.fetch import book_info, book_thumbs


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
        _acl_user

    Internal functions:
        _create_routes(routes, wrapper)

    Route callback functions:
        _clbk_hello
        _clbk_login
        _clbk_logout
        _clbk_thumb
        _clbk_allbooks
    """

    _scramble_shift = {
        # added_scramble_key (obfuscation, not encryption)
        "thumb": 9804,
        "file": 4893,
        "user": 1089,
        "book": 8266,
        "author": 4987,
        "series": 1991,
    }

    def __init__(self, sqlite_file):  # todo: review access control wrappers
        self._db = CatalogueDB(sqlite_file)
        self._persistent_cfg = DBKeyValueStorage(
            self.db.connection,
            "app_config",
            "option",
            "value")
        self._info_init()
        self._db_init()
        self._first_user = self._persistent_cfg.get("init_user")
        self._app = Bottle()
        self._session_manager = SessionManager(self.db.connection)
        self._datadir = os.path.dirname(os.path.abspath(sqlite_file))

        routes_no_acl = (
            ("/login", self._clbk_login, ["GET", "POST"]),
            ("/static/<filename:path>", self._clbk_static),
        )
        routes_after_init = (
            ("/ajax/complete", self._clbk_ajax_complete),
            ("/ajax/fill", self._clbk_ajax_info),
            ("/ajax/suggest", self._clbk_ajax_suggestions),
            ("/books", self._clbk_allbooks),
            ("/books/<hexid>", self._clbk_book),
            ("/books/<hexid>/edit", self._clbk_editbook, ["GET", "POST"]),
            ("/books/add", self._clbk_editbook, ["GET", "POST"]),
            ("/file/<hexid>", self._clbk_user_file),
            ("/logout", self._clbk_logout),
            ("/table/<table>", self._clbk_table),
            ("/thumbs/<hexid>", self._clbk_thumb),
        )
        routes_for_user = (
            ("/queue", self._clbk_queue_barcode),
            ("/", self._clbk_hello),
            ("/quit", self.close),
        )
        self._create_routes(routes_no_acl)
        self._create_routes(routes_after_init, self._acl_not_firstrun)
        self._create_routes(routes_for_user, self._acl_user)

        for code in [404,]:
            self.app.error(code)(self._error_page)

    def _db_init(self):
        """
        Initialize some database entries and create first administrator account
        """
        options = self._persistent_cfg
        if not options.get("init_date"):
            credentials = ("admin_" + random_str(2,4).upper(), random_str(6,8))
            root = self.adduser(
                credentials[0],
                credentials[1],
                datetime.now() + timedelta(days=1))

            for name in ("admin", "user"):
                group = Group(self.db)
                group.name = name
                group.save()
                group.connect(root)

            msg = "Created initial administrative account:\n Login: %s\n Password: %s"
            message(msg % credentials)

            options["init_date"] = timestamp()
            options["init_user"] = ":".join(credentials)

    def suggest(self, field, input, count=10):
        """
        Return suggestions based on user input
        """
        translate = {
            # form_field: (db_table, db_column)
            "title": ("books", "name"),
            "author": ("authors", "name"),
            "publisher": ("books", "publisher"),
            "in_type": ("books", "in_type"),
            "in_comment": ("books", "in_comment"),
            "out_type": ("books", "out_type"),
            "out_comment": ("books", "out_comment"),
            "series_type": ("series", "type"),
            "series_name": ("series", "name"),
            "tags": ("tags", "name")
        }

        result = list()
        if field in translate:
            table, column = translate[field]
            result = self.db.getsuggestions(str(input), table, column, count)
        return result

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
        WILDCARD = "*"  # single char

        #limit, offset = int(limit), int(offset)  # todo: add support for this

        search = re.sub(r"\s+", " ", search).strip()
        search = re.sub(r"[^\d\w %s]" % WILDCARD, "", search).lower()
        old_words = search.split(" ")
        words = list()
        for i in range(len(old_words)):
            new_word = old_words[i]
            if new_word:
                if new_word[0] != WILDCARD:
                    new_word = " " + new_word
                if new_word[-1] != WILDCARD:
                    new_word = new_word + " "
                words.append(new_word.strip(WILDCARD))
        where_clause = " AND ".join("instr(info, ?)>0" for w in words)

        if not sort_keys:
            sort_keys = ("in_date DESC",)
        order_clause = ", ".join(sort_keys)

        query = "SELECT DISTINCT id FROM search_books WHERE %s ORDER BY %s" % (
            where_clause, order_clause)

        count = 0
        books_generator = ()
        if words:
            cur = self.db.sql.generic(
                self.db.connection,
                query,
                params=tuple(words))
            results = cur.fetchall()
            count = len(results)
            books_generator = (self.db.getbook(row["id"]) for row in results)
        return count, books_generator

    def adduser(self, username, password, expiration=None):
        """
        Create new WebUI user

        Returns User() instance
        Raises sqlite3.IntegrityError if username is already taken
        """
        user = User(self.db)
        user.name = username
        user.password = password
        user.expires_on = expiration
        user.save()
        return user

    def __del__(self):
        self.close()

    def _create_routes(self, routes, wrapper=None):
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

    def read_cookie(self, name="auth"):
        COOKIE_MAX_AGE = 2*24*60*60  # seconds

        cookie = request.get_cookie(name, secret=self._cookie_secret)
        data = self.session.get(cookie)

        valid = self.session.valid(cookie)
        valid_age = valid and data[1] + COOKIE_MAX_AGE > timestamp()
        if valid and not valid_age:
            self.session.pop(cookie)
            response.delete_cookie(name)

        return valid and valid_age, data

    def _acl_user(self, func):
        """Wrapper for callback functions. Checks authorization for normal users"""
        @self._acl_not_firstrun
        def with_acl(*a, **ka):
            valid, session = self.read_cookie()
            if valid:
                return func(*a, **ka)
            else:
                url, params = request.urlparts[2:4]
                url = url[1:]
                if url in {"login", "logout", "quit"}: url = ""
                if params: url += "?" + params
                if url:
                    to = "?" + urllib.parse.urlencode({"to":url})
                else:
                    to = str()
                redirect("/login" + to)
        return with_acl

    def _acl_not_firstrun(self, func):
        """Wrapper for _acl_* functions that require app initialization"""
        def with_init(*a, **ka):
            if not self._first_user:
                return func(*a, **ka)
            else:
                return template(
                    "first_run",
                    credentials=self._first_user.split(":"),
                    info=self.info)
        return with_init

    def _info_init(self):
        i = self._info = DynamicDict()
        self._info_ro = ReadOnlyDict(self._info)
        i["books_count"] = lambda: self._persistent_cfg.get("book_count", 0)
        i["copyright"] = lambda: "2016-%s" % datetime.now().year
        i["date_format"] = "%d.%m.%Y"
        i["date"] = lambda: datetime.now().strftime(i["date_format"])

    @property
    def db(self):
        """CatalogueDB object. Used for storing persistent data"""
        return self._db

    @property
    def app(self):
        """Bottle application"""
        return self._app

    @property
    def session(self):
        """SessionManager() object"""
        return self._session_manager

    @property
    def info(self):
        """Access the dictionary with some basic stats and other information"""
        return self._info_ro

    def start(self, config, browser=False, *a, **kw):
        """Start WebUI"""
        self._scramble_key = int(config.id_key)
        self._cookie_secret = str(config.cookie_key)
        self._static_location = str(config.static_dir)
        self._uploads = FSKeyFileStorage(
            os.path.join(self._datadir, str(config.uploads_dir)),
            max_filesize=10*2**20)
        TEMPLATE_PATH.insert(
            0, os.path.join(self._datadir, str(config.templates_dir)))

        class IDReader(object):
            pass
        self.id = IDReader()
        for key in self._scramble_shift:
            setattr(self.id, key, LinCrypt(
                self._scramble_key + self._scramble_shift[key]))

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
            id = self.id.thumb.decode(hexid)
            picture = Thumbnail(self.db, id).image
        except ValueError:
            abort(404, "Invalid thumnail ID: %s" % hexid)
        response.content_type = "image/jpeg"
        return picture

    def _clbk_hello(self):
        return "Hello World!"

    def _clbk_login(self):
        """
        Save [user_id, timestamp] pairs as session information after verifying
        login credentials
        """
        params = request.query.decode()
        to = params.get("to", "")
        
        valid, cookie = self.read_cookie()
        if valid:
            redirect("/" + to)
        else:
            err_status = False
            form = request.forms.decode()
            user = form.get("user")
            password = form.get("password")
            if user and password:
                row = self.db.sql.select("users", {"name": user}).fetchone()
                if row:
                    saved_user = User(self.db, row["id"])
                    if saved_user.check(password):
                        cookie = self.session.new([saved_user.id, timestamp()])
                        response.set_cookie(
                            "auth",
                            cookie,
                            secret=self._cookie_secret)
                        self._persistent_cfg["init_user"] = None
                        self._first_user = None
                        redirect("/" + to)
                else:
                    err_status = True
            elif request.method == "POST":
                err_status = True
            return template("login_password", info=self.info, error=err_status)

    def _clbk_logout(self):
        cookie = request.get_cookie("auth", secret=self._cookie_secret)
        try:
            self.session.pop(cookie)
        except KeyError:
            pass
        response.delete_cookie("auth")
        redirect("/")

    def _clbk_static(self, filename):
        return static_file(
            filename,
            root=os.path.join(self._datadir, self._static_location))

    def _clbk_table(self, table):
        try:
            return template("table",
                cursor=self.db.sql.select(table),
                title=table,
                info=self.info)
        except sqlite3.OperationalError:
            abort(404, "Table `%s` not found in %s" % (table, self.db.filename))

    def _clbk_user_file(self, hexid):
        id = self.id.file.decode(hexid)
        link = BookFile(self.db, id)
        try:
            name, type = link.name, link.type
        except ValueError:
            abort(404, "File not found: %s" % hexid)
        path = self._uploads["BookFile:%s" % id]
        return static_file(
            os.path.basename(path),
            root=os.path.dirname(path),
            download=urllib.parse.quote(name),  # wsgiref encodes to iso-8859-1
            mimetype=type)

    def _clbk_ajax_suggestions(self):
        """Reply to AJAX requests for input suggestions"""
        params = request.query.decode()
        line, field = params.get("q"), params.get("f")
        suggestions = self.suggest(field, line)
        return json.dumps({field: suggestions})

    def _clbk_ajax_complete(self):
        """Reply to AJAX requests for input completion"""
        params = request.query.decode()
        line, field = params.get("q"), params.get("f")
        completion = self.suggest(field, line, 1)
        return json.dumps({field: completion})

    def _clbk_ajax_info(self):
        """Reply to AJAX requests for book info"""
        params = request.query.decode()
        isbn = params.get("isbn")
        thumbs = params.get("thumbs")
        if thumbs:
            return json.dumps(book_thumbs(isbn))
        else:
            return json.dumps(book_info(isbn))

    def _clbk_allbooks(self):
        MAX_PAGE_SIZE = 100
        DEFAULT_PAGE_SIZE = 3

        params = request.query.decode()
        pagenum, pagesize = params.get("p", 0), params.get("ps", DEFAULT_PAGE_SIZE)

        pagenum = max(0, int(pagenum))
        pagesize = min(MAX_PAGE_SIZE, int(pagesize))
        offset = pagenum * pagesize

        query = "SELECT id FROM books ORDER BY last_edit DESC LIMIT ? OFFSET ?"
        search = self.db.sql.generic(
                    self.db.connection,
                    query,
                    params=(pagesize, offset))

        return self._page_book_list(
            search,
            "Все книги",
            pg_info=[pagenum, pagesize])

    def _page_book_list(self, search, title, pg_info):
        return template(
            "book_list",
            books=(self.db.getbook(row[0]) \
                   for row in self.db.sql.iterate(search)),
            title=title,
            pg_info=pg_info,
            info=self.info,
            id=self.id)

    def _clbk_book(self, hexid):
        try:
            id = self.id.book.decode(hexid)
        except ValueError:
            abort(404, "Invalid book id: %s" % hexid)

        book = self.db.getbook(id)
        if book and book.saved:
            return template(
                "book",
                info=self.info,
                book=book,
                id=self.id)
        else:
            abort(404, "Invalid book id: %s" % hexid)

    def _clbk_queue_barcode(self):
        valid, cookie = self.read_cookie()
        user = User(self.db, cookie[0])
        if request.method == "GET":
            params = request.query.decode()
            isbn = params.get("isbn")
            reply = str()
            if params.get("delete") and isbn:
                brcode = self.db.get(Barcode, "isbn", ISBN(isbn).number)
                if brcode: brcode.delete()
                redirect(request.urlparts[2])
            elif isbn:
                brcode = Barcode(self.db)
                try:
                    brcode.isbn = isbn
                    brcode.save()
                except ValueError:
                    reply = "[Error] Invalid ISBN: %s" % isbn
                except sqlite3.IntegrityError:
                    reply = "[OK] Already exists: %s" % isbn
                else:
                    brcode.connect(user)
                    reply = "[OK] ISBN saved to queue: %s" % isbn
            query = "SELECT id FROM barcode_queue ORDER BY date DESC"
            search = self.db.sql.generic(
                self.db.connection,
                query)
            barcodes = (Barcode(self.db, row[0]) \
                        for row in self.db.sql.iterate(search))
            return template(
                "queue",
                barcodes=barcodes,
                message=reply,
                info=self.info)
        elif request.method == "POST":
            pass

    def _clbk_editbook(self, hexid=None):
        book = NoneMocker()
        if hexid:
            b = self.db.getbook(id=self.id.book.decode(hexid))
            if b.saved: book = b

        if request.method == "GET":
            params = request.query.decode()
            input_isbn = params.get("isbn")
            prefill = None
            if input_isbn and not book:
                isbn = ISBN(input_isbn)
                if isbn.valid:
                    input_book = self.db.getbook(isbn=isbn.number)
                    if input_book.saved:
                        redirect("/books/%s" % self.id.book.encode(input_book.id))
                    else:
                        prefill = isbn.number

            conn = dict()
            conn["authors"] = book.getconnected(Author)
            conn["series"] = book.getconnected(Series)
            for item in conn:
                if not conn[item]:
                    conn[item] = [NoneMocker(),]
            conn["files"] = book.getconnected(BookFile) or []
            conn["tags"] = book.getconnected(Tag) or []
            conn["thumbnail"] = list(book.getconnected(Thumbnail) or [])

            return template(
                "book_edit",
                book=book,
                conn=conn,
                id=self.id,
                prefill=prefill,
                info=self.info)
        else:
            if not book: book = self.db.getbook()
            form = request.forms  # "multipart/form-data" doesn't need .decode()

            # 3-tuples: attr name, input name, validator function
            inputs = (("name", "title", validate.nonempty),
                      ("isbn", "isbn", validate.isbn),
                      ("publisher", "publisher", validate.nonempty),
                      ("year", "year", validate.year),
                      ("price", "price", validate.positive),
                      ("annotation", "annotation", validate.nonempty),
                      ("in_date", "in_date", validate.date),
                      ("in_type", "in_type", validate.nonempty),
                      ("in_comment", "in_comment", validate.nonempty),
                      ("out_date", "out_date", validate.date),
                      ("out_type", "out_type", validate.nonempty),
                      ("out_comment", "out_comment", validate.nonempty))

            for attr, input, func in inputs:
                valid, value = func(form.get(input))
                if valid:
                    setattr(book, attr, value)

            try:
                book.save()
            except sqlite3.IntegrityError as e:
                raise e  # todo: handle error

            for author in book.getconnected(Author):
                book.disconnect(author)
            for name in form.getall("author"):
                name = name.strip()
                if name:
                    author = self.db.getauthor(name)
                    if author:
                        author.save()
                        try:
                            book.connect(author)
                        except sqlite3.IntegrityError as e:
                            raise e  # todo: handle error

            for s in book.getconnected(Series):
                book.disconnect(s)
            for type, name, num, total in zip(
                form.getall("series_type"),
                form.getall("series_name"),
                form.getall("book_no"),
                form.getall("total")
            ):
                series = self.db.getseries(name)
                if series:
                    valid_type, type = validate.nonempty(type)
                    if valid_type and not series.saved:
                        series.type = type
                    valid_total, total = validate.positive(total)
                    if valid_total and total:
                        series.number_books = total
                    valid_num, num = validate.positive(num)
                    try:
                        series.save()
                    except sqlite3.IntegrityError as e:
                        raise e  # todo: handle exception
                    if not valid_num: num = None
                    book.connect(series, num)

            for t in book.getconnected(Tag):
                book.disconnect(t)
            for tag in parse_csv(form.get("tags", "")):
                if tag:
                    t = self.db.gettag(tag)
                    t.save()
                    t.connect(book)

            url = None
            pic = request.files.get("thumbnail")
            if pic: pic = pic.file
            if not pic:
                url = form.get("thumb_url")
                if not url:
                    url = form.get("thumb_radio")
                if url:
                    try:
                        req = urllib.request.Request(
                            url,
                            data=None,
                            headers={"User-Agent":"Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36"})
                        pic = urllib.request.urlopen(req)
                        if not pic.headers.get_content_maintype() == "image":
                            debug("not an image: %s" % url)
                            pic = None
                    except Exception as e:
                        raise e  # todo: notify user that fetching failed
            if pic:
                for old_pic in book.getconnected(Thumbnail):
                    book.disconnect(old_pic)
                thumb = Thumbnail(self.db)
                if url: thumb.url = url
                thumb.image = pic
                thumb.save()
                thumb.connect(book)

            for file_hex in form.getall("delete_file"):
                file = BookFile(self.db, self.id.file.decode(file_hex))
                book.disconnect(file)
            for upload in request.files.getall("upload"):
                fo = BookFile(self.db)
                fo.name = upload.raw_filename
                fo.type = upload.content_type
                fo.save()
                try:
                    self._uploads["BookFile:%s" % fo.id] = upload.file
                except Exception as e:
                    fo.delete()
                    raise e  # todo: handle error
                try:
                    book.connect(fo)
                except sqlite3.IntegrityError as e:
                    raise e  # todo: handle error

            redirect("/books/%s" % self.id.book.encode(book.id))

    def _error_page(self, error):
        return template("error_http", info=self.info, error=error)


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


class SessionManager(object):
    """
    Manage sessions for WebUI

    Sessions are stored as cookie:data pairs of strings.
    cookie
        Unique random string
    data
        JSON formatted session data. Data structure should be kept as simple
        as possible to avoid unexpected serialization errors
    """
    def __init__(self, db=None):
        # _sessions object should be a key-value storage for strings,
        # for example dict() or DBKeyValueStorage()
        self._sessions = DBKeyValueStorage(
            db,
            "sessions",
            "cookie",
            "session")

    def get(self, cookie, default=None):
        """Get data corresponding to a cookie"""
        try:
            return json.loads(self._sessions[cookie])
        except KeyError:
            return default

    def new(self, data):
        """Save new session. Return corresponding cookie string"""
        while True:  # make sure key never repeats accidentally
            key = random_str(16, 32)
            if key not in self._sessions: break
        self._sessions[key] = json.dumps(data)
        return key

    def pop(self, cookie):
        """Remove stored session represented by JSON string"""
        return self._sessions.pop(cookie)

    def valid(self, cookie):
        """Check if a cookie string represents a valid session"""
        return cookie in self._sessions
