# HomeLibraryCatalog
Web application for cataloging home books collection


# Unfinished project!
This project is in the early stages of development, most of the time it doesn't 
even start and if it starts it might do something unexpected and irreversible

Consider yourself warned


# Requirements
* **python3** with following packages (available via `pip install`
    * **bottle** - micro web framework with built-in simple web server
    * **pillow** - image manipulation library
    * **lxml** - HTML scraping library


# Priority tasks
* Add book form
* Annotations
* DB clean start


# To Do
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
- [ ] handle clean start
    - [x] create database
    - [x] create administrator account
    - [ ] show initial password via webui
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
    - [ ] add user
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
- [x] delete SQLite.cursor property? = no, it's used for unusual queries

#### Write unit tests?
- [ ] mock database object (or in :memory:)

#### Auto fetcher:
- [ ] annotations
- [ ] thumbnails
