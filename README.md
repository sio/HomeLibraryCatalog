# HomeLibraryCatalog
Web application for cataloging home books collection


# Unfinished project!
This project is in the early stages of development, most of the time it doesn't
even start and if it starts it might do something unexpected and irreversible

Consider yourself warned


# Requirements
* **python3** with following packages (available via `pip install`)
    * **bottle** - micro web framework with built-in simple web server
    * **pillow** - image manipulation library
    * **lxml** - HTML scraping library


# Installation and usage
This application doesn't require installation, just unzip it and start

To start it with default settings launch `HomeLibraryCatalog.py`

Configuration file is named `hlc.config` and is located in the same directory
as the `HomeLibraryCatalog.py` by default


# Top priority todo items
* Add book form
    * thumbnail
        * upload file
        * get image by url
        * auto fetcher
    * series [+]
        * multiple inputs in one line: type, name, # of ##
* Annotations
* DB clean start


# Todo list
#### Ajax suggestions:
- [x] implement input suggestions
- [ ] support more (all?) form fields
- [ ] dropdown design with CSS

#### Settings:
- [x] test json without quotes = invalid according to spec
- [ ] refer to all settings from code

#### Database:
- [x] more fields in `users` table: name, registration date
- [x] user pics? = no
- [x] add field for annotations in `books`

#### SessionManager:
- [ ] reimplement API
- [ ] persistent sessions in database?
- [ ] dictionary cookie->User?
- [ ] save more items to cookie tuple?

#### WebUI:
- [ ] check password expiration on login
- [x] encoding to utf8 in headers? = by default
- [ ] robots.txt file
- [ ] webbrowser.open() always opens IE, replace with default browser
- [x] unique cookie secret for every instance of WebUI (or every URL?)
      = no. Cookie secret is set per app in settings.json
- [x] unique scramble_key for every database (filename?) = no. settings
- [ ] remove bottle.debug
- [ ] CSS:
    - [ ] dark background, light page
    - [ ] no #000000
    - [ ] narrow pages
    - [ ] stylesheet themes
- [ ] Forms:
    - [ ] add user (set password expiration date)
    - [ ] edit user
    - [ ] add book
    - [ ] edit book
    - [ ] add review
    - [ ] book not in library anymore
    - [ ] search box
    - [ ] advanced search: single field searches
    - [ ] force password change if expired
- [ ] Pages:
    - [ ] annotated list with previews
        - [ ] all books
        - [ ] available books
        - [ ] search results
        - [ ] future books (to buy)
        - [ ] recent books with thumbnails (last month, prev-next links)
    - [ ] plain table: title, authors, series, - in series, year
    - [ ] one book
    - [ ] one author
        - [ ] wikipedia link
        - [ ] series "foo"
        - [ ] other books by year
    - [ ] authors/series list
    - [ ] login page, handle invalid auth data
    - [ ] thumbnail upload page

#### Deployment
- [ ] try pyinstall

#### Write unit tests?
- [ ] mock database object (or in :memory:)

#### Auto fetcher:
- [ ] annotations
- [ ] thumbnails


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
