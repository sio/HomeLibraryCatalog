"""
Command-line user interface for HomeLibraryCatalog
"""

import os
import sys
import hlc
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
        "port": 8080,
        "cookie_key": "SET YOUR OWN UNIQUE cookie_key AND id_key IN CONFIG!!!",
        "id_key": 72911,
        },
    "db": {
        "filename": "database.sqlite",
        },
    }


def wsgi_app(json_file, run=False):
    """Create WSGI application for HomeLibraryCatalog"""
    config = settings(os.path.abspath(json_file), DEFAULT_CONFIGURATION)
    VERBOSITY[0] = int(config.app.verbosity)
    if not config.app.root:
        config.app.root = os.path.dirname(hlc.__file__)
    if not os.path.isabs(config.app.data_dir):
        config.app.data_dir = os.path.join(
            os.path.abspath(os.path.dirname(json_file)),
            config.app.data_dir)
    if not os.path.isabs(config.app.logfile):
        config.app.logfile = os.path.join(
            config.app.data_dir,
            config.app.logfile)
    try:
        os.makedirs(config.app.data_dir, exist_ok=True)
    except FileExistsError as e:
        pass

    if run:
        stdout = sys.stdout
        stderr = sys.stderr
        log = open(config.app.logfile, "a", buffering=1, encoding="utf-8")
        sys.stdout = log
        sys.stderr = sys.stdout

    dbfile = os.path.join(config.app.data_dir, config.db.filename)
    ui = WebUI(dbfile, config)
    debug(config)

    if run:
        ui.app.run(
            debug=VERBOSITY[0]>8,
            reloader=False,
            host=config.webui.host,
            port=config.webui.port)
        sys.stdout = stdout
        sys.stderr = stderr
        log.close()
    else:
        return ui


def test():
    """Run all unit tests for HomeLibraryCatalog"""
    import hlc.test
    hlc.test.run()


def main(argv):
    """
    Command-line interface for HomeLibraryCatalog

    Possible arguments are:
    <config.json>
        HomeLibraryCatalog configuration file in JSON format. Missing parameters
        will be read from default configuration
    -t, --tests
        Run unit tests
    """
    if set(("--tests", "-t")).intersection(set(argv)):
        test()
    elif len(argv) in {1, 2}:
        try:
            file = argv[1]
        except IndexError:
            file = "hlc.config"
        wsgi_app(file, run=True)
    else:
        print("Usage: %s <config.json>" % os.path.basename(__file__))
        print(main.__doc__)
        exit(1)


if __name__ == "__main__":
    main(sys.argv)
