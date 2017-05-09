"""
Tools for fetching book info by ISBN
"""

import lxml.html
import urllib.request
import re
from hlc.items import ISBN
from hlc.util import alphanumeric, fuzzy_str_eq


def book_info(isbn):
    """
    Try all available fetchers until full information about book is fetched
    """
    fetchers = (Fantlab,)
    result = dict()
    for fetcher in fetchers:
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

    def __init__(self, isbn):
        self._info = None
        i = ISBN(isbn)
        if i.valid:
            self._isbn = i.number
        else:
            self._isbn = None

    def request(self, url):
        """
        Open URL and return a file-like object if it points to html page
        Raise FetcherInvalidPageError otherwise
        """
        req = urllib.request.Request(
            url,
            data=None,
            headers={"User-Agent": self.USER_AGENT}
        )
        opened = None
        try:
            opened = urllib.request.urlopen(req)
        except urllib.request.URLError as e:
            pass
        if opened and opened.headers.get_content_type() == "text/html":
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

    def fetch_url(self, url):
        page = self.request(url)
        if page: return page.read()

    @property
    def info(self):
        if self._info is None:
            self.get()
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

