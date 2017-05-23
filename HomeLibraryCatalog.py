#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
from hlc import WebUI, debug, settings, VERBOSITY


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
        "uploads_dir": "uploads",
        "cookie_key": "SET YOUR OWN UNIQUE cookie_key AND id_key IN CONFIG!!!",
        "id_key": 72911,
        },
    "db": {
        "filename": "database.sqlite",
        },
    }


def main():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    config = settings(CONFIG_FILE, DEFAULT_CONFIGURATION)
    VERBOSITY[0] = int(config.app.verbosity)

    stdout = sys.stdout
    stderr = sys.stderr
    sys.stdout = open(config.app.logfile, "a", buffering=1, encoding="utf-8")
    sys.stderr = sys.stdout

    test_dbfile = os.path.join(config.app.data_dir, config.db.filename)
    ui = WebUI(test_dbfile)
    ui.start(
        browser=False,
        debug=VERBOSITY[0]>8,
        reloader=VERBOSITY[0]>8,
        host=config.webui.host,
        port=config.webui.port,
        config=config.webui)

    sys.stdout = stdout
    sys.stderr = stderr

    
def test():
    import hlc.test
    hlc.test.run()
    

if __name__ == "__main__":
    args = set(sys.argv)
    if set.intersection(set(("--tests", "-t")), args):
        test()
    else:
        main()
