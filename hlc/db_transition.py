"""
Transition CatalogueDB from previous versions
"""

from .db import CatalogueDB, DBKeyValueStorage


def version(catalogue_db, set_version=None):
    """Get/set version of catalogue_db (plain incrementing integers)"""
    options = DBKeyValueStorage(
                    catalogue_db.connection,
                    "app_config",
                    "option",
                    "value")
    if not options.get("init_date"):
        raise ValueError("CatalogueDB not initialized")
    if set_version:
        options["schema_version"] = int(set_version)
    return int(options.get("schema_version", 0))


def upgrade(catalogue_db, to_version=None):
    """Incrementally upgrade CatalogueDB to latest version"""
    if to_version is None:
        to_version = CatalogueDB._schema_version
    while version(catalogue_db) < to_version:
        upgrade_next(catalogue_db)


def upgrade_next(catalogue_db, transitions=None):
    """
    Upgrade CatalogueDB schema to the next version

    Arguments:
    catalogue_db
        CatalogueDB instance that needs to be upgraded
    transitions
        Transition information dictionary. Keys are schema versions, values
        are lists of SQL statements required to upgrade to this version from
        the one immediately before it. Uses SCHEMA_TRANSITIONS by default
    """
    if transitions is None:
        transitions = SCHEMA_TRANSITIONS

    this_version = version(catalogue_db)
    next_version = None
    for ver in sorted(transitions.keys()):
        if ver > this_version:
            next_version = ver
            break

    if next_version:
        print("Upgrading CatalogueDB to version {}".format(next_version))
        cursor = catalogue_db.connection.cursor()
        try:
            for query in transitions[next_version]:
                print(query.strip())
                cursor.execute(query)
        except Exception as e:
            cursor.connection.rollback()
            raise e
        else:
            cursor.connection.commit()
        version(catalogue_db, next_version)
        print("Succefully upgraded CatalogueDB to version {}".format(next_version))
    else:
        print("CatalogueDB is already at the latest version")


SCHEMA_TRANSITIONS = {
    # version: [sql_statement1, sql_statement2 ...]
    2: [
        """
        DROP VIEW search_books
        """,
        """
        CREATE VIEW search_books AS
        SELECT
            books.id as id,
            " " || simplify(printf("%s %s %s %s", books.name, books.isbn, authors.name, series.name)) || " " as info,
            books.in_date as in_date,
            books.year as year,
            books.name as title,
            authors.name as author,
            books.last_edit as last_edit
        FROM
        books
        LEFT JOIN book_authors ON book_authors.book_id = books.id
        LEFT JOIN authors ON book_authors.author_id = authors.id
        LEFT JOIN book_series ON book_series.book_id = books.id
        LEFT JOIN series ON series.id = book_series.series_id
        """,
    ],
}
