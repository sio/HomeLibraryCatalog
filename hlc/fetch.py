"""
Tools for fetching book info by ISBN
"""

import urllib.request
import re
import json
import logging
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
from scrapehelper.fetch import BaseDataFetcher, DataFetcherError
from .fetcher_cache import CachedObject
from .items import ISBN
from .util import alphanumeric, fuzzy_str_eq, random_str


threads = ThreadPoolExecutor()
log = logging.getLogger(__name__)


def _execute(fetcher):
    '''Worker for concurrent execution'''
    fetcher.info
    return fetcher


def book_info(isbn):
    """
    Try all available fetchers until full information about book is fetched
    """
    jobs = set()
    for fetcher in INFO_FETCHERS:
        jobs.add(threads.submit(_execute, fetcher(isbn)))

    result = dict()
    for job in as_completed(jobs):
        fetcher = job.result()
        if not result:
            result = fetcher.info
        else:
            old, new = result[fetcher.isbn], fetcher.info[fetcher.isbn]
            for k in new.keys():
                if k not in old:
                    old[k] = new[k]
        if fetcher.isfull(result):
            break
    return result


def book_thumbs(isbn):
    """
    Try to fetch as many thumbnails as possible

    It is safe to append general purpose fetchers to THUMB_FETCHERS list.
    Those fetchers' results will be stripped of all extra information except
    for thumbnail urls
    """
    jobs = set()
    for fetcher in THUMB_FETCHERS:
        jobs.add(threads.submit(_execute, fetcher(isbn)))

    result = dict()
    key = 'thumbnail'
    for job in as_completed(jobs):
        fetcher = job.result()
        if not result:
            result = {fetcher.isbn: {}}
        old, new = result[fetcher.isbn], fetcher.info[fetcher.isbn]
        if key not in old and key in new:
            old[key] = new[key]
        elif isinstance(new.get(key), list) \
        and isinstance(old.get(key), list):
            old[key] += new[key]
    old[key] = list(set(old[key]))  # Remove duplicates if any
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


class _UnionMeta(type(BaseDataFetcher), type(CachedObject)):
    '''Joined metaclass for BookInfoFetcher'''
    def __init__(cls, *a, **ka):
        type(BaseDataFetcher).__init__(cls, *a, **ka)
        type(CachedObject).__init__(cls, *a, **ka)


class BookInfoFetcher(BaseDataFetcher, CachedObject, metaclass=_UnionMeta):
    """
    Base class for metadata fetchers
    Child classes have to provide get() method
    """
    USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 \
    (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36"

    def getbook():
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
        Open URL and return a response object if it points to html page
        Raise FetcherInvalidPageError otherwise
        """
        try:
            response = self.get(url)
        except DataFetcherError as e:
            response = None
        if response and response.headers.get('content-type') == content_type:
            return response
        else:
            if not response:
                raise FetcherInvalidPageError("nothing was fetched from %s" % url)
            else:
                raise FetcherInvalidPageError("fetched content is not %s but %s" % (
                            content_type,
                            response.headers.get('content_type')
                        ))

    def parse(self, url):
        """
        Open url and parse it with lxml. Returns None if parsing fails
        """
        try:
            tree = self.parse_html(url)
        except (FetcherInvalidPageError, DataFetcherError) as e:
            tree = None
        return tree

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
        """
        This property should be preferred when reading ISBN metadata,
        because it does not query remote host on every access.
        """
        if self._info is None and self.isbn:
            debug_info = dict(isbn=self.isbn, fetcher=self.__class__.__name__)
            log.debug('Requesting {isbn} with {fetcher}'.format(**debug_info))
            self._info = self.getbook()
            log.debug('>> Fetched {isbn} with {fetcher}'.format(**debug_info))
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


class Libex(BookInfoFetcher):
    """
    Online marketplace for new and used books based in Russia
    """
    _url_pattern = 'https://www.libex.ru/search/result/?pattern=isbn%3A{}'
    HOME = 'https://www.libex.ru'
    year_pattern = re.compile(r'(\d{4})\s*г\.', re.IGNORECASE)

    @property
    def url(self):
        return self._url_pattern.format(self.isbn)

    def parse(self, url):
        try:
            return self.parse_html(url, headers={'Referer': self.HOME})
        except (FetcherInvalidPageError, DataFetcherError):
            return None

    def getbook(self):
        result = dict()
        book = result[self.isbn] = dict()

        search = self.parse(self.url)
        if search is None:
            return result

        match = search.cssselect('table big a')
        if not match:
            return result

        book_page = self.parse(match[0].get('href'))
        if book_page is None:
            return result

        book_card = book_page.xpath(
                    '(//table[@cellspacing=2][@cellpadding=0][//h3[@class="nomargin"]])'
                    '[1]/..'
        )
        if not book_card:
            return result
        book_card = book_card[0]

        title = book_card.xpath('//h1[@class="nomargin"][1]//text()')
        if title:
            book['title'] = title

        authors = book_card.xpath('//h3[@class="nomargin"][1]/a//text()')
        if authors:
            book['authors'] = authors

        publisher = book_card.xpath('//td[contains(text(), "Издательство:")]//text()')
        if publisher:
            publisher = publisher[0]
            parts = publisher.split(';')
            for part in parts:
                if 'Издательство:' in part:
                    book['publisher'] = part.split(':')[-1].strip()
                    break

        year = book_card.xpath('//td[a[contains(text(), "Переплет")]]//text()')
        if year:
            found = self.year_pattern.search(' '.join(year))
            if found:
                book['year'] = found.group(1)

        img = book_card.xpath('//img[@title][@width=60]/@src')
        if img:
            book['thumbnail'] = img

        about = book_card.xpath('//h3[text()="Аннотация"]/following-sibling::p/text()')
        if about:
            book['annotation'] = ''.join(about)

        return result


class ChitaiGorod(BookInfoFetcher):
    """
    Russian online book store, offers both fiction and non-fiction books
    """
    _url_pattern = "https://www.chitai-gorod.ru/search/result.php?q=%s"
    _url_frontpage = "https://www.chitai-gorod.ru"
    _api_url = "https://www.chitai-gorod.ru/search.php"
    _api_host = "www.chitai-gorod.ru"
    _img_url = "https://img-gorod.ru"

    RATELIMIT_CALLS = 5

    def api_get_isbn(self, isbn=None):
        if isbn is None: isbn = self.isbn

        # API payload copied from Chrome Developer Tools.
        # Don't know what this payload means, don't need to know:
        # we need just one query after all.
        # This payload and POST target were discovered by pasting ISBN into
        # search box and looking for autosuggest events in Developer tools.
        payload = "index=goods&query=__ISBN__&type=common&per_page=18&get_count=false"

        # Changing this into self.post() call triggers scrape detection on the
        # remote.
        # Possible cause is that `requests` does not provide a way to specify
        # origin_req_host (one that I know of).
        # Another possible cause might be persisting cookies: maybe the remote
        # allows the first API request without cookies, but no subsequent ones.
        api = urllib.request.Request(
                url=self._api_url,
                headers={
                    "Host": self._api_host,
                    "Origin": self._url_frontpage,
                    "User-Agent": self.USER_AGENT,
                    "Referrer": self.url,
                    "X-Requested-With": 'XMLHttpRequest',
                    "DNT": 1,
                },
                data=payload.replace("__ISBN__", self.isbn).encode("utf-8"),
                origin_req_host=self._url_frontpage,
                method="POST")
        kwargs = dict()
        try:
            kwargs["context"] = ssl._create_unverified_context()
        except AttributeError:
            # Older Python versions do not check SSL certificates by default
            pass
        with self.rate_limit:
            opened = urllib.request.urlopen(api, **kwargs)
        if opened:
            data = json.loads(opened.read().decode("utf-8"))
        else:
            data = dict()
        return data

    def getbook(self):
        result = dict()
        book = result[self.isbn] = dict()

        try:
            api_reply = self.api_get_isbn()
        except Exception:
            api_reply = dict()

        api_data = None
        if api_reply.get("hits", {}).get("total", 0) > 0:
            api_data = api_reply.get("hits",
                                     {}).get("hits",
                                             [{}])[0].get("_source")
        if api_data:
            title = api_data.get("name")
            if title: book["title"] = title

            authors_line = api_data.get("author_t")
            authors = list()
            if authors_line:
                authors = [self.reverse_name(a) \
                           for a in self.split_names(authors_line)]
            elif 'author_detail' in api_data:
                authors_num = len(api_data.get('author', '').split(','))
                authors = [
                    name.replace(' ', ', ', 1)
                    for name in api_data['author_detail'][authors_num:authors_num*2]
                ]
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
            if 'preview' in api_data:
                url = api_data['preview']
                for suffix in (url, url.replace('preview.jpg', 'detail.jpg')):
                    thumbnails.append('/'.join((self._img_url, suffix)))
            if thumbnails: book["thumbnail"] = thumbnails

            annotation = api_data.get("detail_text", '').strip('"')
            if annotation: book["annotation"] = annotation

        return result


class OpenLibrary(BookInfoFetcher):
    """
    OpenLibrary has an extensive library card catalog (primarily for english
    language books), but lacks API access to annotations and offers mediocre
    cover images.
    """
    _url_pattern = "https://openlibrary.org/api/books?bibkeys=ISBN:%s&format=json&jscmd=data"

    def getbook(self):
        result = dict()
        book = result[self.isbn] = dict()
        try:
            reply = self.request(self.url, "application/json")
        except FetcherInvalidPageError:
            reply = None
        if reply is not None:
            try:
                reply = reply.json()
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

            year = reply.get("publish_date", '')
            year = re.findall(r'\d{4}', year)
            if year: book["year"] = year[0]

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
    """
    Livelib is Russian online books catalog offering both fiction and
    non-fiction books. It has high quality cover art and well-written
    annotations.
    """
    #
    # Livelib doesn't like repeated automated requests, so we drop it from
    # INFO_FETCHERS list
    #

    _url_pattern = "https://www.livelib.ru/find/books/%s"
    HOME = "https://www.livelib.ru"
    title_pattern = re.compile(r'^.*«(.*)».*$')

    def parse(self, url):
        try:
            return self.parse_html(
                        url,
                        headers={'Referer': self.HOME},
                        force_encoding='utf-8',
            )
        except (FetcherInvalidPageError, DataFetcherError):
            return None

    def getbook(self):
        result = dict()
        book = result[self.isbn] = dict()
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
            if title: book["title"] = self.title_pattern.sub(r'\1', title)

            authors = self.query_selector(root, ".author-name")
            if authors:
                authors = [self.reverse_name(n) for n in self.split_names(authors)]
            if authors: book["authors"] = authors

            publisher = self.query_selector(root, "span[itemprop=publisher]")
            if publisher:
                publisher = re.sub(r"\s+", " ", publisher).strip()
            if publisher: book["publisher"] = publisher

            year_node = root.xpath('//td[b[text()="Год издания:"]]/following-sibling::td//text()[1]')
            for year in year_node:
                try:
                    year = int(year.strip())
                except Exception as e:
                    continue
                book["year"] = str(year)
                break

            thumbnail = self.query_selector(root, "#main-image-book", attr="src")
            if thumbnail:
                book["thumbnail"] = [thumbnail, self.fix_thumb_url(thumbnail)]

            annotation = self.query_selector(root, "#full-description")
            if annotation: annotation = annotation.strip()
            if annotation: book["annotation"] = annotation

            series = list()
            edition = self.query_selector(root, '.edition-data')
            if edition and hasattr(edition, 'xpath'):
                publ_series = edition.xpath('//a[contains(@href, "/pubseries/")]//text()')
                for name in publ_series:
                    if name.strip():
                        series.append((
                            "издательская серия",
                            name.strip()))
                author_series = edition.xpath('//a[contains(@href, "/series/")]//text()')
                for name in author_series:
                    if name.strip():
                        series.append((
                            "цикл",
                            *name.strip().split(', книга №')))
                if series: book["series"] = series

        return result

    @staticmethod
    def fix_thumb_url(url):
        url = re.sub(r"(boocover/[^/]*/)[^/]*", r"\1o", url)
        url = url.replace(".jpg", ".jpeg")
        return url


class Fantlab(BookInfoFetcher):
    """
    Fantlab offers a vast collection of science fiction books metadata, mostly
    in Russian. It also has an extensive database of old (1980-1990s) Russian
    ISBNs, which are difficult to find elsewhere.
    """
    _url_pattern = "http://fantlab.ru/searchmain?searchstr=%s"

    def getbook(self):
        """Scrape website for information about the book"""
        result = dict()
        book = result[self.isbn] = dict()

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
            for a in root.cssselect('*[itemprop="author"]'):
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
    def getbook(self):
        result = dict()
        book = result[self.isbn] = dict()

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
    """
    Amazon offers quality thumbnails for its products. Other metadata is
    not on par: poor grammar, transliterated descriptions, etc. make it
    unreliable.
    """
    _url_pattern = "https://www.amazon.com/gp/search/ref=sr_adv_b/?search-alias=stripbooks&field-isbn=%s"

    @staticmethod
    def img_urlfix(url):
        filename = url.split("/")[-1]
        newname = re.sub(r"\.[^\.]*(\.[^\.]*$)", r"\1", filename)
        return url[:url.rfind(filename)] + newname

    def getbook(self):
        result = dict()
        book = result[self.isbn] = dict()

        root = self.parse(self.url)
        if root is not None:
            img = root.cssselect("img.s-image")
            if img is not None:
                try:
                    img_url = img[0].get("src")
                except IndexError:
                    pass
                else:
                    img_url = self.img_urlfix(img_url)
                    book["thumbnail"] = [img_url,]
        return result


# Lists of enabled data fetchers. Order does not matter.
# INFO_FETCHERS: data from the fastest source gets shown to user.
# THUMB_FETCHERS: all data sources are queried for wider selection.
INFO_FETCHERS = [Fantlab, Libex, ChitaiGorod, OpenLibrary, Livelib]
THUMB_FETCHERS = INFO_FETCHERS + [AmazonThumb]
