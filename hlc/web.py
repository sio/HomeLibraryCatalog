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
from threading import get_ident
from datetime import datetime, timedelta
from bottle import Bottle, TEMPLATE_PATH, request, abort, response, \
                   template, redirect, static_file
from hlc.items import NoneMocker, Author, User, Thumbnail, ISBN, Group, Series,\
                      BookFile, Tag, Barcode
from hlc.db import CatalogueDB, DBKeyValueStorage, FSKeyFileStorage
from hlc.util import LinCrypt, timestamp, debug, random_str, message, \
                     DynamicDict, ReadOnlyDict, parse_csv, time2unix
from hlc.fetch import book_info, book_thumbs


class WebUI(object):
    """
    Interactive user interface. Starts its own web server, saves user input to
    database.

    Methods:
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

    def __init__(self, sqlite_file, config):
        self._connections = ThreadItemPool(CatalogueDB, sqlite_file)
        self._info_init()
        self._db_init()
        self._app = Bottle()
        self._first_user = self.option.get("init_user")
        self._datadir = os.path.dirname(os.path.abspath(sqlite_file))
        self._info["title"] = config.app.title
        self._scramble_key = int(config.webui.id_key)
        self._cookie_secret = str(config.webui.cookie_key)
        self._static_location = os.path.join(config.app.root, "ui", "static")
        self._uploads = FSKeyFileStorage(
            os.path.join(self._datadir, "uploads"),
            max_filesize=10*2**20)
        TEMPLATE_PATH.insert(
            0, os.path.join(config.app.root, "ui", "templates"))

        class IDReader(object):
            pass
        self.id = IDReader()
        for key in self._scramble_shift:
            setattr(self.id, key, LinCrypt(
                self._scramble_key + self._scramble_shift[key]))

        routes_no_acl = (
            ("/login", self._clbk_login, ["GET", "POST"]),
            ("/static/<filename:path>", self._clbk_static),
        )
        routes_after_init = (
            ("/", self._clbk_frontpage),
            ("/authors/<hexid>", self._clbk_books_author),
            ("/books", self._clbk_books_all),
            ("/books/<hexid>", self._clbk_book),
            ("/series/<hexid>", self._clbk_books_series),
            ("/thumbs/<hexid>", self._clbk_thumb),
            ("/tag/<name>", self._clbk_books_tag),
        )
        routes_user = (
            ("/file/<hexid>", self._clbk_user_file),
            ("/logout", self._clbk_logout),
            ("/users/<name>", self._clbk_user_page),
            ("/users/<name>/edit", self._clbk_user_page, ["GET", "POST"]),
        )
        routes_librarian = (
            ("/ajax/complete", self._clbk_ajax_complete),
            ("/ajax/fill", self._clbk_ajax_info),
            ("/ajax/suggest", self._clbk_ajax_suggestions),
            ("/books/add", self._clbk_book_edit, ["GET", "POST"]),
            ("/books/<hexid>/edit", self._clbk_book_edit, ["GET", "POST"]),
            ("/queue", self._clbk_queue_barcode),
        )
        routes_admin = (
            ("/books/<hexid>/delete", self._clbk_book_delete),
            ("/quit", self.close),
            ("/table/<table>", self._clbk_table),
            ("/admin/users", self._clbk_admin_users, ["GET", "POST"]),
            ("/admin/groups", self._clbk_admin_groups, ["GET", "POST"]),
        )
        for route_list, wrapper in (
                (routes_no_acl, None),
                (routes_after_init, self._acl_not_firstrun),
                (routes_user, self._acl_user),
                (routes_librarian, self._acl_librarian),
                (routes_admin, self._acl_admin),
            ):
            self._create_routes(route_list, wrapper)

        http_error_handler = self._acl_not_firstrun(self._clbk_error_http)
        for code in [404, 403]:
            self.app.error(code)(http_error_handler)

    def __call__(self, *a, **ka):
        return self.app(*a, **ka)

    def __del__(self):
        self.close()

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

    def pagination_params(self, default_size=10, max_size=100):
        """Read pagination parameters from GET request"""
        params = request.query.decode()
        page_num = params.get("p", 0)
        page_size = params.get("ps", default_size)
        page_num = max(0, int(page_num))
        page_size = min(max_size, int(page_size))
        offset = page_num * page_size
        return page_num, page_size, offset

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
            "tags": ("tags", "name"),
            "groups": ("groups", "name"),
        }

        result = list()
        if field in translate:
            table, column = translate[field]
            result = self.db.getsuggestions(str(input), table, column, count)
        return result

    def _acl_admin(self, func):
        """Restrict access to callbacks to administators only"""
        allowed_gid = {1,}  # hardcoded to save database queries
        return self._acl_groups(func, allowed_gid)

    def _acl_librarian(self, func):
        """Restrict access to callbacks to administators only"""
        allowed_gid = {1, 2}  # hardcoded to save database queries
        return self._acl_groups(func, allowed_gid)

    def _acl_groups(self, func, group_ids):
        """Generic access control for certain groups of users"""
        @self._acl_user
        def restricted(*a, **ka):
            current_ids = set(ka["user"].getconnected_id(Group))
            allow_ids = set(group_ids)
            if current_ids.intersection(allow_ids):
                return func(*a, **ka)
            else:
                abort(403, "You have no permissions to view this page")
        return restricted

    def _acl_user(self, func):
        """Wrapper for callback functions. Checks authorization for normal users"""
        @self._acl_not_firstrun
        def with_user(*a, **ka):
            if ka.get("user"):
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
        return with_user

    def _acl_not_firstrun(self, func):
        """Wrapper for _acl_* functions that require app initialization"""
        def with_init(*a, **ka):
            if not self._first_user:
                valid, session = self.read_cookie()
                if valid:
                    user = User(self.db, session[0])
                    ka["user"] = user
                return func(*a, **ka)
            else:
                return template(
                    "first_run",
                    credentials=self._first_user.split(":"),
                    info=self.info)
        return with_init

    def _clbk_admin_generic(self, cls, field, **kw):
        if not kw.get("attr"): kw["attr"] = field

        if kw.get("add"):
            new = cls(self.db)
            setattr(new, kw["attr"], kw["add"])
            new.save()

        query = "SELECT %s FROM %s ORDER BY %s"
        search = self.db.sql.generic(
            self.db.connection,
            query,
            (cls.__IDField__, cls.__TableName__, field))
        kw["items"] = (cls(self.db, row[0]) \
                       for row in self.db.sql.iterate(search))
        return template("accounts", info=self.info, **kw)

    def _clbk_admin_groups(self, user=None):
        return self._clbk_admin_generic(
            cls=Group,
            title="Группы пользователей",
            field="name",
            add=request.forms.decode().get("add"),
            user=user)

    def _clbk_admin_users(self, user=None):
        return self._clbk_admin_generic(
            cls=User,
            title="Пользователи",
            field="name",
            link=["/users/%s", "name"],
            add=request.forms.decode().get("add"),
            user=user)

    def _clbk_ajax_complete(self, user=None):
        """Reply to AJAX requests for input completion"""
        params = request.query.decode()
        line, field = params.get("q"), params.get("f")
        completion = self.suggest(field, line, 1)
        return json.dumps({field: completion})

    def _clbk_ajax_info(self, user=None):
        """Reply to AJAX requests for book info"""
        params = request.query.decode()
        isbn = params.get("isbn")
        thumbs = params.get("thumbs")
        if thumbs:
            return json.dumps(book_thumbs(isbn))
        else:
            return json.dumps(book_info(isbn))

    def _clbk_ajax_suggestions(self, user=None):
        """Reply to AJAX requests for input suggestions"""
        params = request.query.decode()
        line, field = params.get("q"), params.get("f")
        suggestions = self.suggest(field, line)
        return json.dumps({field: suggestions})

    def _clbk_book(self, hexid, user=None):
        book = self._get_book(hexid)
        full_view = user and {1,2}.intersection(set(user.getconnected_id(Group)))
        repeat = bool(request.query.decode().get("repeat"))
        return template(
            "book",
            info=self.info,
            book=book,
            id=self.id,
            user=user,
            repeat=repeat,
            full=full_view)

    def _clbk_book_delete(self, hexid, user=None):
        book = self._get_book(hexid)
        book.delete()
        redirect(request.urlparts[2])

    def _clbk_book_edit(self, hexid=None, user=None):
        book = NoneMocker()
        if hexid:
            book = self._get_book(hexid)

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
                info=self.info,
                user=user)
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
                repeat = self.db.getbook(
                    isbn=validate.isbn(form.get("isbn"))[1])
                if repeat.saved:
                    redirect("/books/%s?repeat=yes" % 
                             self.id.book.encode(repeat.id))
                else:
                    raise e  # is there any chance execution gets here?

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

    def _clbk_books_all(self, user=None):
        query = "SELECT id FROM books ORDER BY last_edit DESC LIMIT ? OFFSET ?"
        pg_info = self.pagination_params()
        search = self.db.sql.generic(
                    self.db.connection,
                    query,
                    params=pg_info[1:])
        return template(
            "book_list",
            books=(self.db.getbook(row[0]) \
                   for row in self.db.sql.iterate(search)),
            title="Все книги",
            pg_info=pg_info[:2],
            info=self.info,
            id=self.id,
            user=user)

    def _clbk_books_author(self, hexid, user=None):
        author = Author(self.db, self.id.author.decode(hexid))
        if not author.saved: abort(404)
        query = """
            SELECT book_id
            FROM (
               SELECT book_id FROM book_authors WHERE author_id = ?
            ) as conn LEFT JOIN books ON conn.book_id = books.id
            ORDER BY books.year ASC, books.last_edit ASC
            LIMIT ? OFFSET ?
            """
        pg_info = self.pagination_params(default_size=25)
        search = self.db.sql.generic(
                    self.db.connection,
                    query,
                    params=[author.id,] + list(pg_info[1:]))
        return template(
            "author",
            books=(self.db.getbook(row[0]) \
                   for row in self.db.sql.iterate(search)),
            title=author.name.replace(",", ""),
            pg_info=pg_info[:2],
            info=self.info,
            id=self.id,
            user=user)

    def _clbk_books_tag(self, name, user=None):
        tag = self.db.get(Tag, "name", name)
        if not tag.saved: abort(404)
        query = """
            SELECT book_id
            FROM (
               SELECT book_id FROM book_tags WHERE tag_id = ?
            ) as conn LEFT JOIN books ON conn.book_id = books.id
            ORDER BY books.year ASC, books.last_edit ASC
            LIMIT ? OFFSET ?
            """
        pg_info = self.pagination_params(default_size=25)
        search = self.db.sql.generic(
                    self.db.connection,
                    query,
                    params=[tag.id,] + list(pg_info[1:]))
        return template(
            "series",
            books=(self.db.getbook(row[0]) \
                   for row in self.db.sql.iterate(search)),
            title=tag.name,
            pg_info=pg_info[:2],
            info=self.info,
            id=self.id,
            user=user)

    def _clbk_books_series(self, hexid, user=None):
        series = Series(self.db, self.id.series.decode(hexid))
        if not series.saved: abort(404)
        query = """
            SELECT book_id
            FROM (
               SELECT book_id FROM book_series WHERE series_id = ?
            ) as conn LEFT JOIN books ON conn.book_id = books.id
            ORDER BY books.year ASC, books.last_edit ASC
            LIMIT ? OFFSET ?
            """
        pg_info = self.pagination_params(default_size=25)
        search = self.db.sql.generic(
                    self.db.connection,
                    query,
                    params=[series.id,] + list(pg_info[1:]))
        return template(
            "series",
            books=(self.db.getbook(row[0]) \
                   for row in self.db.sql.iterate(search)),
            title=series.name,
            pg_info=pg_info[:2],
            info=self.info,
            id=self.id,
            user=user)

    def _clbk_error_http(self, error, user=None):
        return template("error_http", info=self.info, error=error, user=user)

    def _clbk_frontpage(self, user=None):
        redirect("/books")  # todo: create proper front page

    def _clbk_login(self, user=None):
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
                        self.option["init_user"] = None
                        self._first_user = None
                        if saved_user.expired:
                            redirect("/users/%s/edit" % saved_user.name)
                        else:
                            redirect("/" + to)
                    else:
                        err_status = True
                else:
                    err_status = True
            elif request.method == "POST":
                err_status = True
            return template("login_password", info=self.info, error=err_status)

    def _clbk_logout(self, user=None):
        cookie = request.get_cookie("auth", secret=self._cookie_secret)
        try:
            self.session.pop(cookie)
        except KeyError:
            pass
        response.delete_cookie("auth")
        redirect("/")

    def _clbk_queue_barcode(self, user=None):
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

                repeat = self.db.getbook(isbn=isbn)
                if repeat.saved:
                    redirect("/books/%s" % self.id.book.encode(repeat.id))

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
                info=self.info,
                user=user)
        elif request.method == "POST":
            pass

    def _clbk_static(self, filename, user=None):
        return static_file(
            filename,
            root=self._static_location)

    def _clbk_table(self, table, user=None):
        try:
            return template("table",
                cursor=self.db.sql.select(table),
                title=table,
                info=self.info,
                user=user)
        except sqlite3.OperationalError:
            abort(404, "Table `%s` not found in %s" % (table, self.db.filename))

    def _clbk_thumb(self, hexid, user=None):
        """Show thumbnail based on encrypted `hexid`"""
        picture = None
        try:
            id = self.id.thumb.decode(hexid)
            thumb = Thumbnail(self.db, id)
        except ValueError:
            abort(404, "Invalid thumnail ID: %s" % hexid)

        last_modified_unix = time2unix(thumb.last_edit)
        last_modified_utc = datetime.utcfromtimestamp(last_modified_unix)
        last_modified = last_modified_utc.strftime("%a, %d %b %Y %H:%M:%S GMT")
        response.set_header("Last-Modified", last_modified)
        response.set_header("Cache-Control", "public,max-age=%d" % (60*60*24*30))
        response.content_type = "image/jpeg"
        return thumb.image

    def _clbk_user_file(self, hexid, user=None):
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

    def _clbk_user_page(self, name, user=None):
        edit_key = "/edit"
        inputs = {
            "self": {"fullname", "password", "password_repeat"},
            "admin": {"name", "fullname", "groups", "password", "password_repeat"},
            "readonly": {}}
        url = request.urlparts[2]

        subject = self.db.get(User, "name", name)
        admin = user.isconnected(Group(self.db, 1))
        if admin and url.endswith(edit_key):
            access = "admin"
        elif subject == user and url.endswith(edit_key):
            access = "self"
        elif not url.endswith(edit_key):
            access = "readonly"
        else:
            access = None
        edit_link = bool(admin or subject==user)

        if subject and subject.saved:
            if request.method == "GET":
                if access:
                    return template(
                        "user",
                        subject=subject,
                        user=user,
                        access=inputs[access],
                        edit_link=edit_link,
                        info=self.info)
                else:
                    abort(403, "You have no permissions to edit this information")
            elif request.method == "POST":
                form = request.forms.decode()
                def get_input(name, default=None):
                    if name in inputs[access]:
                        return form.get(name)
                    else:
                        return default

                valid, value = validate.nonempty(get_input("name"))
                if valid: subject.name = value

                valid, value = validate.nonempty(get_input("fullname"))
                if valid: subject.fullname = value

                valid, value = validate.nonempty(get_input("password"))
                if valid and get_input("password") == get_input("password_repeat"):
                    subject.password = get_input("password")
                    subject.expires_on = datetime.now() + timedelta(days=365)

                subject.save()

                if "groups" in inputs[access]:
                    for group in subject.getconnected(Group):
                        group.disconnect(subject)
                    for group_name in parse_csv(get_input("groups", "")):
                        group = self.db.get(Group, "name", group_name)
                        if group and group.saved:
                            group.connect(subject)

                redirect("/users/" + subject.name)
            else:
                raise RuntimeError("Invalid method: %s" % request.method)
        else:
            abort(404, "Invalid user name: %s" % name)

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

    def _db_init(self):
        """
        Initialize some database entries and create first administrator account
        """
        options = self.option
        if not options.get("init_date"):
            credentials = ("admin_" + random_str(2,4).upper(), random_str(6,8))
            root = self.adduser(
                credentials[0],
                credentials[1],
                datetime.now() + timedelta(days=1))

            for name in ("admin", "librarian", "visitor"):  # order matters
                group = Group(self.db)
                group.name = name
                group.save()
                group.connect(root)

            msg = "Created initial administrative account:\n Login: %s\n Password: %s"
            message(msg % credentials)

            options["init_date"] = timestamp()
            options["init_user"] = ":".join(credentials)

    def _info_init(self):
        i = self._info = DynamicDict()
        self._info_ro = ReadOnlyDict(self._info)
        i["books_count"] = lambda: self.option.get("book_count", 0)
        i["copyright"] = lambda: "2016-%s" % datetime.now().year
        i["date_format"] = "%d.%m.%Y"
        i["date"] = lambda: datetime.now().strftime(i["date_format"])

    def _get_book(self, hexid):
        try:
            id = self.id.book.decode(hexid)
        except ValueError:
            id = None
        book = self.db.getbook(id)
        if book and book.saved:
            return book
        else:
            abort(404, "Invalid book id: %s" % hexid)

    @property
    def db(self):
        """CatalogueDB object. Used for storing persistent data. Thread-safe"""
        return self._connections.get()

    @property
    def app(self):
        """Bottle application"""
        return self._app

    @property
    def option(self):
        """Access application persistent configuration. Thread-safe"""
        return DBKeyValueStorage(self.db.connection, "app_config", "option", "value")

    @property
    def session(self):
        """Manage user cookie sessions. Thread-safe"""
        return SessionManager(self.db.connection)

    @property
    def info(self):
        """Access the dictionary with some basic stats and other information"""
        return self._info_ro

    def close(self, user=None):
        """Stop WebUI: stop server, close database"""
        self.app.close()
        for conn in self._connections.pool.values():
            conn.close()
        sys.stderr.close()  # not ideal, but I don't know any better


class validate(object):
    """
    A collection of functions for validating user input

    All methods return 2-tuple: boolean status of validation and preprocessed
    value after validation
    """

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
    def isbn(text):
        try:
            valid = ISBN(text).valid
        except Exception:
            valid = False
        return valid, text

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


class ThreadItemPool(object):
    """
    Store objects that should not be shared between threads

    Thread IDs returned by threading.get_ident() may be recycled when thread
    exits and another one is created
    """
    # todo: garbage-collect objects that correspond to outdated IDs
    #       check against [t.ident for t in threading.enumerate()]
    def __init__(self, constructor, *a, **ka):
        def create(): return constructor(*a, **ka)
        self._create = create
        self._stored = dict()

    def get(self):
        thread_id = get_ident()
        try:
            item = self.pool[thread_id]
        except KeyError:
            item = self.pool[thread_id] = self._create()
        return item

    @property
    def pool(self):
        return self._stored
