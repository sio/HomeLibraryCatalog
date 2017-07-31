# HomeLibraryCatalog deployment

## Using wsgiref simple web server
HomeLibraryCatalog runs on the built-in wsgiref WSGIServer() by default. This
non-threading HTTP server is perfectly fine for development and early
production, but may become a performance bottleneck when server load increases.

Also, you should keep in mind, that wsgiref authors do not recommend exposing
it to the whole Internet without some kind of reverse proxy. Reference WSGI
implementation was not written to handle all the security threats that can be
found out in the wild.

To launch HomeLibraryCatalog with wsgiref server run:
```
HomeLibraryCatalog.py /path/to/configuration.json
```
If no argument is passed on command line "hlc.config" in the current working
directory will be used.

Configuration file format is described [here][configuration.md].

## Using WSGI-compatible web server
WSGI (Web Server Gateway Interface) is a specification for simple and universal
interface between web servers and web applications for the Python programming
language (PEP 3333).

There are numerous web servers that support WSGI, from the popular Apache and
Nginx to the less known Tornado and Gunicorn. HomeLibraryCatalog can be run on
any of those.

To create an instance of WSGI-aware application use:
```
from hlc.launcher import wsgi_app
application = wsgi_app("/path/to/configuration.json")
```
Configuration file format is described [here][configuration.md].

After that pass the `application` variable to the web server of your choosing
(please refer to the web server documentation on using custom application).
