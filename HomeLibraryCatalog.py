#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
from hlc import WebUI, debug, settings

CONFIG_FILE = "hlc.config"
DEFAULT_CONFIGURATION = {
    "app": {
        "data_dir": "data",
        "verbosity": 5,
        "logfile": "hlc.log",
        },
    "webui": {
        "host": "127.0.0.1",
        "port": 8888,
        "static_dir": "static",
        "templates_dir": "templates",
        "cookie_key": "1490794018",
        "id_key": 16749726111,
        },
    "db": {
        "filename": "database.sqlite",
        },
    }


def main():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    config = settings(CONFIG_FILE, DEFAULT_CONFIGURATION)

    
    stdout = sys.stdout
    stderr = sys.stderr
    sys.stdout = open(config.app.logfile, "a", buffering=1, encoding="utf-8")
    sys.stderr = sys.stdout

    test_dbfile = os.path.join(config.app.data_dir, config.db.filename)
    ui = WebUI(test_dbfile)
    ui.clean_init()
    ui.start(
        browser=False,
        debug=True,
        reloader=True,
        host=config.webui.host,
        port=config.webui.port,
        config=config.webui)

    sys.stdout = stdout
    sys.stderr = stderr
        
# PRIORITY:
#   * AJAX suggestions
#   * Annotations
#   * DB clean start
#
# TODO:
#   [ ] Settings:
#       [+] test json without quotes = invalid according to spec
#       [ ] refer to all settings from code
#   [ ] Database:
#       [+] more fields in `users` table: name, registration date
#       [+] user pics? = no
#       [+] add field for annotations in `books`
#   [ ] SessionManager:
#       [ ] reimplement API
#       [ ] persistent sessions in database?
#       [ ] dictionary cookie->User?
#       [ ] save more items to cookie tuple?
#   [ ] WebUI:
#       [ ] handle clean start
#           [+] create database
#           [+] create administrator account
#           [+] show initial password via webui
#       [ ] check password expiration on login
#       [+] encoding to utf8 in headers? = by default
#       [ ] robots.txt file
#       [ ] webbrowser.open() always opens IE, replace with default browser
#       [+] unique cookie secret for every instance of WebUI (or every URL?) 
#           = no. Cookie secret is set per app in settings.json    
#       [+] unique scramble_key for every database (filename?) = no. settings
#       [ ] remove bottle.debug
#       [ ] CSS:
#           [ ] dark background, light page
#           [ ] no #000000
#           [ ] narrow pages
#           [ ] stylesheet themes
#       [ ] Forms:
#           [ ] add user
#           [ ] edit user
#           [ ] add book
#           [ ] edit book
#           [ ] add review
#           [ ] book not in library anymore
#           [ ] search box
#           [ ] advanced search: single field searches
#           [ ] force password change if expired
#       [ ] Pages:
#           [ ] annotated list with previews
#               [ ] all books
#               [ ] available books
#               [ ] search results
#               [ ] future books (to buy)
#               [ ] recent books with thumbnails (last month, prev-next links)
#           [ ] plain table: title, authors, series, # in series, year
#           [ ] one book
#           [ ] one author
#               [ ] wikipedia link
#               [ ] series "foo"
#               [ ] other books by year
#           [ ] authors/series list
#           [ ] login page, handle invalid auth data
#           [ ] thumbnail upload page
#       [ ] Ajax:
#           [ ] receive request
#           [ ] send json
#   [ ] Deployment
#       [ ] try pyinstall
#   [+] Delete SQLite.cursor property? = no, it's used for unusual queries
#   [ ] Write unit tests?
#       [ ] mock database object (or in :memory:)
#   [ ] Auto fetcher:
#       [ ] annotations
#       [ ] thumbnails


if __name__ == "__main__":
    main()
