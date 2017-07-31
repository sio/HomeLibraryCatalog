"""
Tools for fetching book info by ISBN
"""

import lxml.html
import urllib.request
import re
import json
import ssl
from hlc.items import ISBN
from hlc.util import alphanumeric, fuzzy_str_eq, debug, random_str


def book_info(isbn):
    """
    Try all available fetchers until full information about book is fetched
    """
    result = dict()
    for fetcher in INFO_FETCHERS:
        f = fetcher(isbn)
        if not result:
            result = f.info
        else:
            old, new = result[f.isbn], f.info[f.isbn]
            for k in new.keys():
                if k not in old:
                    old[k] = new[k]
        if f.isfull(result): break
    return result


def book_thumbs(isbn):
    """
    Try to fetch as many thumbnails as possible

    It is safe to append general purpose fetchers to THUMB_FETCHERS list.
    Those fetchers' results will be stripped of all extra information except
    for thumbnail urls
    """
    result = {ISBN(isbn).number:{}}
    for fetcher in THUMB_FETCHERS:
        f = fetcher(isbn)
        old, new = result[f.isbn], f.info[f.isbn]
        key = "thumbnail"
        if key not in old \
        and key in new:
            old[key] = new[key]
        elif isinstance(new.get(key), list) \
        and isinstance(old.get(key), list):
            old[key] += new[key]
    return result


def get_nested(dictionary, *keys, default=None):
    """Get value from nested dictionary"""
    reply = default
    for key in keys:
        try:
            reply = dictionary[key]
        except KeyError:
            reply = default
            break
        else:
            dictionary = reply
    return reply


class FetcherInvalidPageError(ValueError):
    """Raised when fetched page is not suitable for further parsing"""
    pass


class BookInfoFetcher(object):
    """
    Base class for metadata fetchers
    """
    USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 \
    (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36"
    _page_encoding = "utf-8"  # default encoding for HTML pages

    def get():
        """
        This method has to be provided by child classes.

        get() is meant to return a dictionary of data corresponding to a book
        If any of the fields is not available, such key must not be included in
        the returned dictionary

        Dictionary structure:
        {
            <isbn>: {
                "title": <string>,
                "authors": [<string>, <string>, ...],
                "publisher": <string>,
                "year": <string>,
                "series": [
                    (<type:string>, <name:string>, <#:string>, <##:string>),
                    (<another series tuple>),
                    ...
                ],
                "thumbnail": [<url1:string>, <url2:string>, ...]
                "annotation": <string>,
            }
        }
        """
        raise NotImplementedError("This method has to be implemented by subclass")

    def __init__(self, isbn):
        self._info = None
        i = ISBN(isbn)
        if i.valid:
            self._isbn = i.number
        else:
            self._isbn = None

    def request(self, url, content_type="text/html"):
        """
        Open URL and return a file-like object if it points to html page
        Raise FetcherInvalidPageError otherwise
        """
        req = urllib.request.Request(
            url,
            data=None,
            headers={"User-Agent": self.USER_AGENT})
        opened = None
        try:
            opened = urllib.request.urlopen(req)
        except urllib.request.URLError as e:
            pass
        if opened and opened.headers.get_content_type() == content_type:
            return opened
        else:
            if not opened:
                raise FetcherInvalidPageError("nothing was fetched from %s" % url)
            else:
                raise FetcherInvalidPageError("fetched content is not text/html but %s" %
                    opened.headers.get_content_type())

    def parse(self, url):
        parser = lxml.html.HTMLParser(encoding=self._page_encoding)
        tree = None
        try:
            tree = lxml.html.parse(self.request(url), parser)
        except FetcherInvalidPageError as e:
            pass
        if tree:
            root = tree.getroot()
            root.make_links_absolute(root.base_url)
            return root

    def query_selector(self, node, css, one=True, attr=None):
        found = node.cssselect(css)
        result = list()
        if len(found):
            for item in found:
                if attr:
                    result.append(item.get(attr))
                else:
                    result.append(item.text_content())
                if one: break
        if result and one:
            return result[0]
        else:
            return result

    def fetch_url(self, url):
        page = self.request(url)
        if page: return page.read()

    @property
    def info(self):
        if self._info is None and self.isbn:
            self._info = self.get()
        elif not self.isbn:
            self._info = {self.isbn:{}}
        return self._info

    def isfull(self, input=None):
        if input is None: input = self.info
        required_fields = set((
            "thumbnail",
            "authors",
            "title",
            "publisher",
            "year",
            "annotation",
        ))
        fetched_fields = set(input[self.isbn].keys())

        full = not bool(required_fields - fetched_fields)
        return full

    @property
    def url(self):
        return self._url_pattern % self._isbn

    @property
    def isbn(self):
        return self._isbn

    @staticmethod
    def reverse_name(name):
        """
        Turn 'John Doe' into 'Doe, John'
        If more than two words are given, return unchanged
        """
        names = name.split(" ")
        if len(names) == 2:
            return ", ".join([alphanumeric(n).title() for n in names[::-1]])
        else:
            return name

    @staticmethod
    def split_names(names, separator=","):
        """Turn 'John Doe, Jane Doe, Jack Daniels' into list of names"""
        return [name.strip() for name in names.split(separator)]


class ChitaiGorod(BookInfoFetcher):
    """
    Russian online book store, offers both fiction and non-fiction books
    """
    _url_pattern = "https://www.chitai-gorod.ru/search/result.php?q=%s"
    _url_frontpage = "https://www.chitai-gorod.ru"
    _api_url = "https://search.chitai-gorod.ru/catalog/_search?size=20&from=0"
    _api_host = "search.chitai-gorod.ru"
    _img_url = "https://img-gorod.ru/upload"

    def api_get_isbn(self, isbn=None):
        if isbn is None: isbn = self.isbn

        # API payload copied from Chrome Developer Tools.
        # Don't know what this payload means, don't need to know:
        # we need just one query after all.
        payload = """
            {"query":{"function_score":{"boost_mode":"sum","query":{"bool":
            {"should":[{"filtered":{"query":{"dis_max":{"queries":[
            {"match":{"isbn":{"query":"__ISBN__"}}},{"match":
            {"isbn":{"query":"__ISBN__"}}}],"tie_breaker":0.9}}}}]}}}},
            "aggs":{"sect":{"terms":{"field":"ibl_sec_id","size":500}},
            "author":{"terms":{"field":"author.raw","size":50}},"author_b":
            {"terms":{"field":"author_b","size":50}},"author_t":{"terms":
            {"field":"author_t.raw","size":50}}},"sort":[{"_score":{"order":
            "desc"}}],"min_score":1.15}
            """

        api = urllib.request.Request(
                url=self._api_url,
                headers={
                    "Host": self._api_host,
                    "Origin": self._url_frontpage,
                    "User-Agent": self.USER_AGENT,
                    "Referrer": self.url,
                },
                data=payload.replace("__ISBN__", self.isbn).encode("utf-8"),
                origin_req_host=self._url_frontpage,
                method="POST")
        nonsecure = ssl._create_unverified_context()
        opened = urllib.request.urlopen(api, context=nonsecure)
        if opened:
            data = json.loads(opened.read().decode("utf-8"))
        else:
            data = dict()
        return data

    def get(self):
        result = dict()
        book = result[self.isbn] = dict()

        try:
            api_reply = self.api_get_isbn()
        except Exception:
            api_reply = dict()

        api_data = None
        if api_reply.get("hits", {}).get("total", 0) == 1:
            api_data = api_reply.get("hits",
                                     {}).get("hits",
                                             [{}])[0].get("_source")
        if api_data:
            title = api_data.get("name")
            if title: book["title"] = title

            authors_line = api_data.get("author_t")
            if authors_line:
                authors = [self.reverse_name(a) \
                           for a in self.split_names(authors_line)]
            else:
                authors_line = api_data.get("author")
                if authors_line:
                    authors = [a.replace(" ", ", ", 1) \
                               for a in self.split_names(authors_line)]
            if authors: book["authors"] = authors

            publisher = api_data.get("publisher")
            if publisher: book["publisher"] = publisher

            year = api_data.get("year")
            if year: book["year"] = int(year)

            series = api_data.get("seria")
            if series: book["series"] = [("цикл", series)]

            thumbnails = list()
            for path_key, name_key in [
                    ("d_pic_path", "d_pic_name"),
                    ("p_pic_path", "p_pic_name"),
                    ]:
                path, name = api_data.get(path_key), api_data.get(name_key)
                if path and name:
                    thumbnails.append("/".join([
                        self._img_url,
                        path,
                        name,
                        ]))
            if thumbnails: book["thumbnail"] = thumbnails

            annotation = api_data.get("content")
            if annotation: book["annotation"] = annotation

        return result


class OpenLibrary(BookInfoFetcher):
    _url_pattern = "https://openlibrary.org/api/books?bibkeys=ISBN:%s&format=json&jscmd=data"

    def get(self):
        result = dict()
        book = result[self._isbn] = dict()
        try:
            reply = self.request(self.url, "application/json")
        except FetcherInvalidPageError:
            reply = None
        if reply is not None:
            try:
                reply = json.loads(reply.read().decode("utf-8"))
            except Exception:
                reply = dict()
            if reply: reply = reply.popitem()[1]

            title = reply.get("title")
            if title: book["title"] = title

            authors = list()
            for a in reply.get("authors", list()):
                name = a.get("name")
                if name:
                    authors.append(self.reverse_name(name))
            if not authors:
                name = reply.get("by_statement")
                if name: authors.append(name)
            if authors: book["authors"] = authors

            publisher = reply.get("publishers")
            if publisher: publisher = publisher[0].get("name")
            if publisher: book["publisher"] = publisher

            year = reply.get("publish_date")
            if year: book["year"] = year

            thumbnail = None
            for path in [
                    ("cover", "large"),
                    ("cover", "medium"),
                    ("cover", "small")]:
                thumbnail = get_nested(reply, *path)
                if thumbnail:
                    book["thumbnail"] = [thumbnail,]
                    break
        return result


class Livelib(BookInfoFetcher):
    #
    # Livelib doesn't like repeated automated requests, so we drop it from
    # INFO_FETCHERS list
    #

    _url_pattern = "https://www.livelib.ru/find/books/%s"

    def get(self):
        result = dict()
        book = result[self._isbn] = dict()
        root = self.parse(self.url)

        true_url = ""
        if root is not None:
            for anchor in root.cssselect("#objects-block .object-edition a.title"):
                url = anchor.get("href")
                if "book" in url:
                    true_url = url
                    break

        root = None
        if true_url:
            root = self.parse(true_url + "-" + random_str(10, 20))
        if root is not None:
            title = self.query_selector(root, "#book-title")
            if title: book["title"] = title

            authors = self.query_selector(root, ".author-name")
            if authors:
                authors = [self.reverse_name(n) for n in self.split_names(authors)]
            if authors: book["authors"] = authors

            publisher = self.query_selector(root, "span[itemprop=publisher]")
            if publisher:
                publisher = re.sub(r"\s+", " ", publisher).strip()
            if publisher: book["publisher"] = publisher

            year_node = root.xpath('//span[@itemprop="isbn"]/following-sibling::b[1]/following-sibling::text()[1]')
            for year in year_node:
                try:
                    year = int(year.strip())
                except Exception as e:
                    year = None
                if year: book["year"] = str(year)

            series = list()
            publ_series = self.query_selector(root, "#book-series a", one=False)
            for name in publ_series:
                if name.strip():
                    series.append((
                        "издательская серия",
                        name.strip()))
            author_series = self.query_selector(root, "#work-cycle a", one=False)
            for name in author_series:
                if name.strip():
                    series.append((
                        "цикл",
                        name.strip()))
            if series: book["series"] = series

            thumbnail = self.query_selector(root, "#main-image-book", attr="src")
            if thumbnail:
                book["thumbnail"] = [thumbnail, self.fix_thumb_url(thumbnail)]

            annotation = self.query_selector(root, "#full-description")
            if annotation: annotation = annotation.strip()
            if annotation: book["annotation"] = annotation

        return result

    @staticmethod
    def fix_thumb_url(url):
        url = re.sub(r"(boocover/[^/]*/)[^/]*", r"\1o", url)
        url = url.replace(".jpg", ".jpeg")
        return url


class LivelibThumb(Livelib):
    def get(self):
        result = dict()
        book = result[self._isbn] = dict()
        root = self.parse(self.url)

        true_url = ""
        if root is not None:
            for anchor in root.cssselect("#objects-block .object-edition a.title"):
                url = anchor.get("href")
                if "book" in url:
                    true_url = url
                    break

        root = None
        if true_url:
            root = self.parse(true_url + "-" + random_str(10, 20))
        if root is not None:
            thumbnail = self.query_selector(root, "#main-image-book", attr="src")
            if thumbnail:
                book["thumbnail"] = [thumbnail, self.fix_thumb_url(thumbnail)]
        return result


class Fantlab(BookInfoFetcher):
    _url_pattern = "http://fantlab.ru/searchmain?searchstr=%s"

    def get(self):
        """Scrape website for information about the book"""
        result = dict()
        book = result[self._isbn] = dict()

        # search results page
        root = self.parse(self.url)
        true_url = ""
        if root is not None:
            for anchor in root.cssselect("div.one a"):
                if "edition" in anchor.get("href"):
                    true_url = anchor.get("href")
                    break

        # edition page
        root = None
        if true_url:
            root = self.parse(true_url)
        if root is not None:
            title_nodes = root.cssselect('*[itemprop="name"]')
            if len(title_nodes):
                book["title"] = title_nodes[0].text_content()

            authors = list()
            for a in root.cssselect('*[itemprop="author"] a'):
                authors.append(self.reverse_name(a.text_content()))
            if authors: book["authors"] = authors

            publ_nodes = root.cssselect('*[itemprop="publisher"] a')
            if len(publ_nodes):
                book["publisher"] = publ_nodes[0].text_content()

            year_nodes = root.cssselect('*[itemprop="copyrightYear"]')
            if len(year_nodes):
                book["year"] = year_nodes[0].text_content()

            series_nodes = root.xpath('//div[contains(@class,"main-info-block-detail")]//a[contains(@href,"series")]')
            series_nodes += root.xpath('//div[contains(@class,"main-info-block-detail")]//a[contains(@data-href,"series")]')
            series = list()
            for node in series_nodes:
                series.append(("издательская серия", node.text_content()))
            description = root.xpath(
                '//p[b[contains(text(),"Описание:")]]/following-sibling::*[1]//a[contains(@href, "work")]')
            for work in description:
                series.append((
                    "цикл",
                    re.sub("""['"«»]""", "", work.text_content())))
            if series: book["series"] = series

            thumb_nodes = root.cssselect('img[itemprop="image"]')
            thumb_urls = list()
            for node in thumb_nodes:
                thumb_urls.append(node.get("src"))
            if thumb_urls:
                book["thumbnail"] = thumb_urls

            book_url = str()
            url_nodes = root.xpath('//div[contains(@class,"main-info-block-detail")]//a[contains(@href,"work")]')
            for node in url_nodes:
                if fuzzy_str_eq(node.text_content(), book.get("title")):
                    book_url = node.get("href")
                    break
            if book_url:
                root = self.parse(book_url)
                if root is not None:
                    annotation_nodes = root.cssselect('*[itemprop="description"]')
                    if len(annotation_nodes):
                        book["annotation"] = annotation_nodes[0].text_content()
        return result


class FantlabThumb(Fantlab):
    """Fetch only thumbnail from Fantlab (less http requests)"""
    def get(self):
        result = dict()
        book = result[self._isbn] = dict()

        root = self.parse(self.url)
        if root is not None:
            images = root.cssselect("div.one img")
            for img in images:
                if "small" in img.get("src"):
                    img_url = img.get("src").replace("small", "big")
                    img_url = img_url.replace("//data.fantlab.ru", "//fantlab.ru")
                    book["thumbnail"] = [img_url,]
                    break
        return result


class AmazonThumb(BookInfoFetcher):
    _url_pattern = "https://www.amazon.com/gp/search/ref=sr_adv_b/?search-alias=stripbooks&field-isbn=%s"

    @staticmethod
    def img_urlfix(url):
        filename = url.split("/")[-1]
        newname = re.sub(r"\.[^\.]*(\.[^\.]*$)", r"\1", filename)
        return url[:url.rfind(filename)] + newname

    def get(self):
        result = dict()
        book = result[self._isbn] = dict()

        root = self.parse(self.url)
        if root is not None:
            img = root.cssselect(".s-item-container img.s-access-image")
            if img is not None:
                try:
                    img_url = img[0].get("src")
                except IndexError:
                    pass
                else:
                    img_url = self.img_urlfix(img_url)
                    book["thumbnail"] = [img_url,]
        return result


# Public API for changing priority of fetchers
INFO_FETCHERS = [Fantlab, ChitaiGorod, OpenLibrary]
THUMB_FETCHERS = [FantlabThumb, ChitaiGorod, AmazonThumb, OpenLibrary]
