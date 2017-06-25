#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
from hlc import WebUI, debug, settings, VERBOSITY


DEFAULT_CONFIGURATION = {
    "app": {
        "data_dir": "data",
        "verbosity": 5,
        "logfile": "hlc.log",
        "root": None
        },
    "webui": {
        "host": "127.0.0.1",
        "port": 8888,
        "cookie_key": "SET YOUR OWN UNIQUE cookie_key AND id_key IN CONFIG!!!",
        "id_key": 72911,
        },
    "db": {
        "filename": "database.sqlite",
        },
    }


def run_app(json_file):
    config = settings(os.path.abspath(json_file), DEFAULT_CONFIGURATION)

    VERBOSITY[0] = int(config.app.verbosity)

    config.app.root = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(config.app.data_dir):
        config.app.data_dir = os.path.join(config.app.root, config.app.data_dir)
    try:
        os.makedirs(config.app.data_dir, exist_ok=True)
    except FileExistsError as e:
        pass

    stdout = sys.stdout
    stderr = sys.stderr
    sys.stdout = open(
        os.path.join(config.app.data_dir, config.app.logfile),
        "a",
        buffering=1,
        encoding="utf-8")
    sys.stderr = sys.stdout

    dbfile = os.path.join(config.app.data_dir, config.db.filename)
    ui = WebUI(dbfile)
    ui.start(
        browser=False,
        debug=VERBOSITY[0]>8,
        reloader=False,
        host=config.webui.host,
        port=config.webui.port,
        config=config)

    sys.stdout = stdout
    sys.stderr = stderr


def test():
    import hlc.test
    hlc.test.run()


def main(argv):
    args = set(argv)
    if set.intersection(set(("--tests", "-t")), args):
        test()
    elif len(argv)==2:
        run_app(argv[1])
    else:
        print("Usage: %s config.file" % os.path.basename(__file__))
        exit(1)

        
if __name__ == "__main__":
    main(sys.argv)
