'''
Interactively test book info fetchers
'''


import json
import hlc.fetch


TEST_BOOKS = (
    '978-569-989-837-4',
    '978-504-094-785-0',
    '978-538-909-894-7',
    '587-198-004-X',
    '978-504-097-209-8', # two authors
    '978-5-699-59223-4', # two authors (more distinct)
    '978-076-531-985-2', # English-first publication
)


def run_tests(fetcher_class, filename=None):
    output = list()
    for isbn in TEST_BOOKS:
        f = fetcher_class(isbn)
        output.append({'isbn': isbn, 'full': f.isfull(), 'info': f.info})
    pretty = json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False)
    if filename:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(pretty)
    else:
        print(pretty)


def main():
    '''Interactive test interface'''
    fetcher = None
    while not fetcher:
        fetcher_name = input('Type the fetcher class name to test: ')
        try:
            fetcher = getattr(hlc.fetch, fetcher_name)
        except Exception:
            pass
    use_file = input('Save output to file instead of stdout? [y/N]: ')
    if use_file and use_file.lower().startswith('y'):
        filename = 'book_fetcher_test.log'
    else:
        filename = None
    run_tests(fetcher, filename)


if __name__ == '__main__':
    main()
