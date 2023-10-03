import logging

from PyQt6.QtCore import QByteArray
from PyQt6.QtSql import QSqlDatabase, QSqlQuery

DB_TYPE = "QSQLITE"
DB_NAME = "../utilities/shows.db"
TABLE_NAME = "shows"
CREATE_TABLE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        start_date TEXT,
        run_time TEXT,
        synopsis TEXT,
        poster BLOB
    )
"""
INSERT_SQL = f"INSERT INTO {TABLE_NAME} (name, start_date, run_time, synopsis, poster) VALUES (?, ?, ?, ?, ?)"
SELECT_SQL = f"SELECT * FROM {TABLE_NAME} WHERE name = ?"


class DbHandler:
    def __init__(self):
        self.db = None
        self.connect()
        self.create()

    def connect(self) -> None:
        """Connect to the SQLite database."""
        self.db = QSqlDatabase.addDatabase(DB_TYPE)
        self.db.setDatabaseName(DB_NAME)

        if not self.db.open():
            logging.error("Failed to connect to database: %s", self.db.lastError().text())
            raise Exception("Failed to connect to database")

        logging.info("Connected to database")

    @staticmethod
    def create() -> None:
        """Create the shows table if it doesn't exist."""
        query = QSqlQuery()
        create_table = CREATE_TABLE_SQL

        if not query.exec(create_table):
            logging.error("Failed to create table: %s", query.lastError().text())
            raise Exception("Failed to create table")

    @staticmethod
    def insert(name: str, start_date: str, run_time: str, synopsis: str, poster: bytes) -> None:
        """Insert show data into the database."""
        query = QSqlQuery()

        query.prepare(INSERT_SQL)
        query.bindValue(0, name)
        query.bindValue(1, start_date)
        query.bindValue(2, run_time)
        query.bindValue(3, synopsis)
        query.bindValue(4, QByteArray(poster))

        if not query.exec():
            logging.error("Error inserting into database: %s", query.lastError().text())
            raise Exception("Failed to insert data into database")

        logging.info(f"Inserted {name} into the database.")

    @staticmethod
    def select(show: dict[str, str]) -> dict[str, str]:
        """Select show data from the database."""
        query = QSqlQuery()
        name = next(iter(show))
        url = show[name]

        query.prepare(SELECT_SQL)
        query.bindValue(0, name)

        if not query.exec():
            logging.error("Error querying the database: %s", query.lastError().text())
            return {}

        if query.next():
            return {
                "name": query.value(1),
                "date": query.value(2),
                "time": query.value(3),
                "synopsis": query.value(4),
                "poster": query.value(5),
                "url": url
            }

        return {}

    def close(self) -> None:
        """Close the database connection."""
        self.db.close()
        logging.info("Connection to database closed")
