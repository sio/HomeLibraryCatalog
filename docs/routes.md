# Routes served by HomeLibraryCatalog
This document describes the intended list of routes to be served by hlc

## Existing routes

### Always available
###### /login
###### /static/`<filename:path>`

### Available after application initialization

### Available after login
###### /
###### /add
###### /ajax/complete
###### /ajax/fill
###### /ajax/suggest
###### /books
###### /books/`<hexid>`
###### /books/`<hexid>`/edit
###### /books/add
###### /file/`<hexid>`
###### /logout
###### /queue`[?isbn=number]`
Save scanned barcodes (ISBNs) for adding to library later. Usecase: scan codes 
on cellphone, edit and save on desktop
###### /thumbs/`<hexid>`

### Administrative routes
###### /quit
###### /table/`<table>`

## Not implemented yet
### Available after login
###### /authors/`<hexid>`
###### /series/`<hexid>`
###### /tag/`<name>`

### Administrative routes
