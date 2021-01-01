from typing import Optional

from bloodwhoresbot.core.database import Database
from bloodwhoresbot.models import User


class UserSystem:
    def __init__(self, db: Database):
        self._db = db
        self._users = db.get_instance().chats

    def get_username(self, user, chat):
        current_user = self.get_user(user.id, chat.id)

        if current_user is None:
            self.add_new_user(user, chat)
            current_user = self.get_user(user.id, chat.id)

        if current_user.emoji is None:
            return user.username

        return f'{user.username} {current_user.emoji}'

    def add_new_user(self, user, chat):
        if self.get_user(user.id, chat.id) is not None:
            return False

        new_user = self._create_user(user, chat)
        self._add_user(new_user)

        return True

    def get_user(self, personal_id, chat_id) -> Optional[User]:
        current_user = self._users.find_one({"personal_id": personal_id, "chat_id": chat_id})

        if current_user:
            return User(**current_user)

        return None

    def _add_user(self, user: User) -> None:
        self._users.insert_one(user.dict())

    def _create_user(self, user, chat) -> User:
        return User(personal_id=user.id, chat_id=chat.id)
