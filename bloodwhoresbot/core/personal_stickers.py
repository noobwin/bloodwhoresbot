from bloodwhoresbot.core.database import Database
from bloodwhoresbot.utils import get_random_file


class PersonalStickers:
    def __init__(self, db: Database):
        self._db = db
        self._personal_stickers = db.get_instance().personalStickers

    def get_random(self, user):
        if self._personal_stickers.find_one({"personal_id": user.id}) is None:
            return None

        return get_random_file(self._personal_stickers, {"personal_id": user.id})
