# HomeLibraryCatalog configuration file
Configuration of HomeLibraryCatalog is done via JSON configuration file supplied
as the only command line argument

Environment variables referenced in string values will be expanded according to
host system's standards

As per JSON specification all keys and string values have to be enclosed in 
double quotes

## Example configuration (with default values)
```
{
    "db": {
        "filename": "database.sqlite"
    },
    "app": {
        "title": "",
        "verbosity": 5,
        "data_dir": "data",
        "logfile": "hlc.log"
    },
    "webui": {
        "host": "127.0.0.1",
        "port": 8080,
        "cookie_key": "SET YOUR OWN UNIQUE cookie_key AND id_key IN CONFIG!!!",
        "id_key": 72911
    }
}
```

## **db** - database settings
### filename
Path to SQLite database. Relative paths are resolved relative to `app.data_dir`
value

Default: database.sqlite

## **app** - application settings (backend)
### title
Name of the library (placed in the header of each page)

### verbosity
Integer. Higher values mean more verbose output. Value of 9 turns on debug
messages

Default: 5

### data_dir
Path to persistent storage directory. Database and users' uploads will be stored
there. Relative paths are resolved relative to the location of JSON config

Default: data

### logfile
Path to log file. Relative paths are resolved relative to `app.data_dir`

Default: hlc.log

## **webui** - web interface settings (frontend)
### host
When running as standalone application, specifies IP address for *wsgiref* to
bind to. Use `0.0.0.0` to listen on all interfaces including the external one

Default: 127.0.0.1

### port
When running as standalone application, specifies port for *wsgiref* to listen 
on. Values below 1024 require root privileges

Default: 8080

### cookie_key
A string used as a key for encrypting cookies. Must not be published. Change the
default value before runninng the application. Changing this value will
invalidate all saved user sessions, but is not harmful otherwise. New sessions
will be initiated after standard login procedures

Default: **do not use default value**

### id_key
Integer used in obfuscating numeric identifiers (book id, author id, etc).
`id_key` should be set up at random before the first launch. Changing this value
will affect urls of existing pages, and may invalidate users bookmarks

Default: 72911