from datetime import datetime, timedelta
from random import choice
from time import sleep

from bloodwhoresbot.core.cheated import Cheated
from bloodwhoresbot.core.database import Database
from bloodwhoresbot.core.intro_stickers import IntroStickers
from bloodwhoresbot.core.user_system import UserSystem
from bloodwhoresbot.models import Message
from bloodwhoresbot.utils import date_to_tuple, get_random_file


class PidorGame:
    DELTA_HOURS = 24
    DELTA_MINUTES = 0
    DELTA_TIME = timedelta(hours=DELTA_HOURS, minutes=DELTA_MINUTES)

    def __init__(self, chat_id: int, db: Database) -> None:
        self._chat_id = chat_id
        self._db = db
        self._user_system = UserSystem(db)
        self._cheated = Cheated(db)
        self._intro_stickers = IntroStickers(db)

        self._timings = db.get_instance()['timings']

    def get_pidor(self):
        timing = self._timings.find_one({"chat_id": self._chat_id, "game": "pidor"})
        return timing['pidor_of_the_day']

    def get_wait_time(self) -> timedelta:
        last_played = self._get_last_played_time()
        now = datetime.now()

        if last_played + self.DELTA_TIME > now:
            return last_played + self.DELTA_TIME - now
        else:
            return timedelta(0)

    def get_intro_messages(self):
        pidor_messages_db = self._db.get_instance().pidorMessages
        pidor_messages = get_random_file(pidor_messages_db, {})

        for text in pidor_messages["intro_messages"]:
            if text == "send_intro_sticker":
                yield Message(text=self._intro_stickers.get_random()["file_id"])
            else:
                yield Message(text=text, parse_mode=pidor_messages["parse_mode"])
            sleep(pidor_messages["sleep_time"])

    def choose_pidor(self) -> None:
        cheated_users = self._cheated.get(self._chat_id)
        if cheated_users:
            pidor = choice(cheated_users)
        else:
            users = self._user_system.get_users(self._chat_id)
            pidor = choice(users)

        self._user_system.inc(pidor, self._chat_id)
        self._set_last_played_time(datetime.now())
        self._set_new_pidor(pidor)

    def get_pidor_message(self, pidor_username: str) -> Message:
        pidor_messages_db = self._db.get_instance()["pidorMessages"]
        pidor_messages = get_random_file(pidor_messages_db, {})

        return Message(text=pidor_messages["winner_message"].format(pidor_username),
                       parse_mode=pidor_messages["parse_mode"])

    def _get_last_played_time(self) -> datetime:
        timing = self._timings.find_one({"chat_id": self._chat_id, "game": "pidor"})
        if timing is None:
            OLD_DATE = (2000, 1, 1, 1, 1, 1)
            self._timings.insert_one({"game": "pidor",
                                      "chat_id": self._chat_id,
                                      "last_run": (2000, 1, 1, 1, 1, 1),
                                      "pidor_of_the_day": None})
            return datetime(*OLD_DATE)

        return datetime(*timing['last_run'])

    def _set_last_played_time(self, time: datetime) -> None:
        self._timings.update_one({"chat_id": self._chat_id, "game": "pidor"},
                                 {"$set": {"last_run": date_to_tuple(time)}})

    def _set_new_pidor(self, pidor_id: int) -> None:
        self._timings.update_one({"chat_id": self._chat_id, "game": "pidor"},
                                 {"$set": {"pidor_of_the_day": pidor_id}})
