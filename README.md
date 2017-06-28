# HomeLibraryCatalog
Web application for cataloging home books collection


# Installation and usage
Installation:
* `pip install git+git://github.com/sio/HomeLibraryCatalog.git` to install
directly from GitHub *or*
* download release archive, and install with `pip install <archive.tar.gz>` *or*
* download release archive, unpack it and start `HomeLibraryCatalog.py`

To launch HomeLibraryCatalog with wsgiref web server run
`HomeLibraryCatalog config.json` where *config.json* is the 
[configuration file][1]. If no command line arguments are supplied,
*hlc.config* in current working directory is used

[1]: docs/configuration.md


# Requirements
* **python3** with following packages (available via `pip install`)
    * **bottle** - micro web framework with built-in simple web server
    * **pillow** - image manipulation library
    * **lxml** with **cssselect** - HTML scraping library


# Localization status
As of now all user interaction happens in Russian

Localization is not planned in the foreseable future due to the lack of human
resources

All locale-dependent text is contained in template files (*.tpl).
Application supports changing template directory via configuration file, so all
locale-specific text can be translated and placed into another directory.
Proper localizations tools and techniques (gettext et al) are not yet supported


# License and copyright
Copyright © 2016-2017 Vitaly Potyarkin
```
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
```


# Todo list
#### WebUI:
- [ ] Barcode queue:
    - [ ] fetch related information in background, store to title field
    - [ ] style /queue page with CSS
    - [ ] do not queue books already in the library
    - [ ] show title and user on /queue page
- [ ] Forms:
    - [ ] for registered users
        - [ ] book review
        - [ ] author rating
        - [ ] book not in library anymore
        - [ ] password change (force if expired)
    - [ ] for administrators
        - [ ] edit groups
    - [ ] for all visitors
        - [ ] search box
        - [ ] advanced search: single field searches
    - [ ] start page: greetings/newest books/thumbnail gallery?
- [ ] Pages:
    - [ ] annotated list with previews
        - [ ] all books
        - [ ] available books
        - [ ] search results
        - [ ] future books (to buy)
        - [ ] recent books with thumbnails (last month, prev-next links)
    - [ ] plain table: title, authors, series, - in series, year
    - [ ] one book
        - [ ] external links
        - [ ] more information?
        - [ ] hide some data from anonymous users
    - [ ] one author
        - [ ] wikipedia link
        - [ ] series "foo"
        - [ ] other books by year
    - [ ] authors/series list
- [ ] CSS:
    - [ ] dark background, light page
    - [ ] no #000000
    - [ ] narrow pages
    - [ ] stylesheet themes
- [ ] check password expiration on login
- [ ] robots.txt file
- [ ] webbrowser.open() always opens IE, replace with default browser

#### Auto fetcher:
- [ ] more sources:
    - [ ] Wordcat
    - [ ] Ozon
    - [ ] Amazon
    - [ ] Google Books?

#### Deployment:
- [ ] try pyinstall

#### Unit tests:
- [ ] mock database object (or in :memory:)

#### Database:
- [ ] add garbage collector method (delete orphaned thumbnails, authors, etc.)
