from pymongo import MongoClient


class Database:
    def __init__(self, username, password, db_name) -> None:
        with open("mongodb_url.txt", "r") as tk:
            token = tk.readline().format(username, password, db_name).rstrip()
            self._db = MongoClient(token)[db_name]

    def get_instance(self):
        return self._db
