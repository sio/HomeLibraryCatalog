'''
Interactively test book info fetchers
'''


from pprint import pprint
from hlc.fetch import *


TEST_BOOKS = (
    '978-569-989-837-4',
    '978-504-094-785-0',
    '978-538-909-894-7',
    '587-198-004-X',
)


def run_tests(fetcher_class, filename=None):
    for isbn in TEST_BOOKS:
        f = fetcher_class(isbn)
        pprint({'isbn': isbn, 'full': f.isfull(), 'info': f.info})
