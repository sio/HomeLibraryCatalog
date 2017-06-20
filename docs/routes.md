# Routes served by HomeLibraryCatalog
This document describes the intended list of routes to be served by hlc

## Existing routes

### Always available
##### /login
##### /static/`<filename:path>`

### Available after application initialization

### Available after login
##### /
Homepage. Not implemented.

Ideas:
* recent additions list
* bookshelf: tiled cover images

##### /ajax/complete
AJAX handler. Returns one suggestion for auto completing while typing

##### /ajax/fill
AJAX handler. Returns book information for filling in add/edit form

##### /ajax/suggest
AJAX handler. Returns multiple suggestions for dropdown selection

##### /books
Paginated list of all books in the library

##### /books/`<hexid>`
Individual book card

##### /books/`<hexid>`/edit
Edit previously saved book. Uses the same input form as `/books/add`

##### /books/add
Form for entering new book information. Requires Javascript (uses AJAX for auto
completion, other JS for interactivity)

##### /file/`<hexid>`
Download attached files

##### /logout
End current user session

##### /queue`[?isbn=number]`
Save scanned barcodes (ISBNs) for adding to library later. Usecase: scan codes
on cellphone, edit and save on desktop.

GET parameters are used to save and delete entries

##### /thumbs/`<hexid>`
View attached cover images. Used mostly internally for embedding images into
web pages

### Administrative routes
##### /quit
Stop application. Closes the database connection and terminates backend

##### /table/`<table>`
View plain database table. For debugging purposes only


## Not implemented yet
### Available after login
##### /authors/`<hexid>`
Author name, some information, some relevant links + list of books by that
author

##### /series/`<hexid>`
Series name, may be some links + list of books in series

##### /tag/`<name>`
List of books by tag


### Administrative routes
##### /admin/adduser
Create new user account. Inputs: login, password, expiration date, groups

##### /admin/groups
View/edit groups: add/delete users, create/delete groups

##### /books/`<hexid>`/delete
Delete a book from the library as if it never existed

##### /users/`<name>`
View user information. Edit user information: change password, change group membership
