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
        "cookie_key": "SET YOUR OWN UNIQUE cookie_key AND id_key IN CONFIG!!!",
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
    ui.start(
        browser=False,
        debug=True,
        reloader=True,
        host=config.webui.host,
        port=config.webui.port,
        config=config.webui)

    sys.stdout = stdout
    sys.stderr = stderr


if __name__ == "__main__":
    main()
