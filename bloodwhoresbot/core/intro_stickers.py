from bloodwhoresbot.core.database import Database
from bloodwhoresbot.utils import get_random_file


class IntroStickers:
    def __init__(self, db: Database):
        self._db = db
        self._intro_stickers = db.get_instance().introStickers

    def get_random(self):
        return get_random_file(self._intro_stickers, {})
