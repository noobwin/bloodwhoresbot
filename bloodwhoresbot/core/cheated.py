from bloodwhoresbot.core.database import Database


class Cheated:
    def __init__(self, db: Database):
        self._db = db
        self._cheated = db.get_instance().cheated

    def get(self, chat_id):
        return list(self._cheated.find({"chat_id": chat_id}))
