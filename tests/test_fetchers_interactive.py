'''
Interactively test book info fetchers
'''


import json
import random
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


def run_tests(fetcher_class):
    output = list()
    for isbn in TEST_BOOKS:
        f = fetcher_class(isbn)
        output.append({'isbn': isbn, 'full': f.isfull(), 'info': f.info})
    return output


def single_fetcher():
    '''Test single fetcher with predefined set of ISBNs'''
    fetcher = None
    while not fetcher:
        fetcher_name = input('Type the fetcher class name to test: ')
        try:
            fetcher = getattr(hlc.fetch, fetcher_name)
        except Exception:
            pass
    output(run_tests(fetcher))


def single_book():
    '''Test single book with all fetchers asyncronously'''
    isbn = input('Type ISBN to test (empty to use predefined): ')
    if not isbn:
        isbn = random.choice(TEST_BOOKS)
    output(hlc.fetch.book_info(isbn))


def output(data):
    '''Print or save output to file. Select interactively'''
    pretty = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
    use_file = input('Save output to file instead of stdout? [y/N]: ')
    if use_file and use_file.lower().startswith('y'):
        filename = 'book_fetcher_test.log'
    else:
        filename = None
    if filename:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(pretty)
    else:
        print(pretty)


def main():
    '''Main menu for manual testing'''
    selected = ''
    options = {
        'f': single_fetcher,
        'b': single_book,
    }
    greeting = 'Which manual test to execute?\n'
    prompt = [greeting] + [
        ' [{key}]: {explained}\n'.format(key=key, explained=value.__doc__)
        for key, value in sorted(options.items())
    ]
    while selected not in options:
        selected = input(''.join(prompt))
        selected = selected.lower()[:1]
    options[selected]()


if __name__ == '__main__':
    main()
