from enum import Enum
from typing import Optional, Any

from pydantic.main import BaseModel

from bloodwhoresbot.core.game import GameEnum


class User(BaseModel):
    _id: Any
    personal_id: int
    chat_id: int
    score: int = 0
    sticker_reading_mode: bool = False
    pua_count: int = 0
    wink_count: int = 0
    emoji: Optional[str] = None


class Context(Enum):
    successful_registration = 'successful_registration'
    already_registered = 'already_registered'
    not_enough_players = 'not_enough_players'
    no_one_is_registered = 'no_one_is_registered'
    reading_stickers_in_conversation = 'reading_stickers_in_conversation'
    start_reading_stickers = 'start_reading_stickers'
    end_of_reading_stickers = 'end_of_reading_stickers'
    sticker_was_added_successfully = 'sticker_was_added_successfully'
    sticker_has_already_been_added = 'sticker_has_already_been_added'
    not_registered = 'not_registered'
    emoji_supplied = 'emoji_supplied'
    still_early_pidor = 'still_early_pidor'
    still_early_piu = 'still_early_piu'
    still_early_pua = 'still_early_pua'
    still_early_wink = 'still_early_wink'


class Answer(BaseModel):
    _id: Any
    context: Context
    message: str
    parse_mode: Optional[str] = None


class Timing(BaseModel):
    _id: Any
    game: GameEnum
    chat_id: int
    personal_id: Optional[int] = None


class Message(BaseModel):
    text: str
    parse_mode: Optional[str] = None
