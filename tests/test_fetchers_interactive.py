'''
Interactively test book info fetchers
'''


from pprint import pprint
import hlc.fetch


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


def main():
    '''Interactive test interface'''
    fetcher = None
    while not fetcher:
        fetcher_name = input('Type the fetcher class name to test: ')
        try:
            fetcher = getattr(hlc.fetch, fetcher_name)
        except Exception:
            pass
    run_tests(fetcher)


if __name__ == '__main__':
    main()
