import datetime
from os import environ
from random import choice
from time import sleep

import telebot
from pymongo import DESCENDING

from bloodwhoresbot.core.answers import Answers
from bloodwhoresbot.core.database import Database
from bloodwhoresbot.core.intro_stickers import IntroStickers
from bloodwhoresbot.core.personal_stickers import PersonalStickers
from bloodwhoresbot.core.user_system import UserSystem
from bloodwhoresbot.models import Context
from bloodwhoresbot.utils import declination_count, get_random_file, text_has_emoji, date_representation, date_to_tuple

# with open("token.txt", "r") as tk:
#     TOKEN = tk.readline()

# with open("mongodb_url.txt", "r") as tk:
#     MONGODB_TOKEN = tk.readline().rstrip()

BOT_TOKEN = environ["TOKEN"]
MONGO_USERNAME = environ["MONGO_USERNAME"]
MONGO_PASSWORD = environ["MONGO_PASSWORD"]
MONGO_DB = environ["MONGO_DB"]

db = Database(MONGO_USERNAME, MONGO_PASSWORD, MONGO_DB)
user_system = UserSystem(db)
answers = Answers(db)
intro_stickers = IntroStickers(db)
personal_stickers = PersonalStickers(db)
timings = db.get_instance()["timings"]

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=["register"])
def echo_register(message):
    chat = message.chat
    user = message.from_user

    if user_system.add_new_user(user, chat):
        result = Context.successful_registration
    else:
        result = Context.already_registered

    answer = answers.get(result)
    bot.send_message(chat.id,
                     answer.message.format(user_system.get_username(user, chat)),
                     parse_mode=answer.parse_mode)


@bot.message_handler(commands=["pidor"])
def echo_pidor(message):
    chats = db.get_instance()["chats"]
    cheated = db.get_instance()["cheated"]
    chat = message.chat

    cheated_participants = [bot.get_chat_member(chat.id, participant["personal_id"]) for participant in
                            cheated.find({"chat_id": chat.id})]

    participants = [bot.get_chat_member(chat.id, participant["personal_id"]) for participant in
                    chats.find({"chat_id": chat.id})]

    if timings.find_one({"chat_id": chat.id, "game": "pidor"}) is None:
        timings.insert_one(
            {"game": "pidor", "chat_id": chat.id, "last_run": None, "delta_hours": 24, "delta_minutes": 0,
             "pidor_of_the_day": None, "label_hours": ["час", "часа", "часов"],
             "label_minutes": ["минута", "минуты", "минут"], "label_seconds": ["секунда", "секунды", "секунд"]})

    if len(participants) <= 0:
        answer = answers.get(Context.not_enough_players)
        bot.send_message(chat.id, answer.message, parse_mode=answer.parse_mode)
        return

    timing = timings.find_one({"chat_id": chat.id, "game": "pidor"})
    current_date = datetime.datetime.now()

    if timing["last_run"] is None or timing["pidor_of_the_day"] is None:
        timings.update_one({"chat_id": chat.id, "game": "pidor"}, {"$set": {"last_run": date_to_tuple(current_date)}})
    else:
        last_run = datetime.datetime(*timing["last_run"])
        delta = datetime.timedelta(hours=timing["delta_hours"], minutes=timing["delta_minutes"])

        if last_run + delta > current_date:
            answer = answers.get(Context.still_early_pidor)
            bot.send_message(chat.id, answer.message.format(
                user_system.get_username(bot.get_chat_member(chat.id, timing["pidor_of_the_day"]).user, chat),
                date_representation(last_run + delta - current_date, timing)), parse_mode=answer.parse_mode)
            return
        else:
            timings.update_one({"chat_id": chat.id, "game": "pidor"},
                               {"$set": {"last_run": date_to_tuple(current_date)}})

    pidor_messages = db.get_instance()["pidorMessages"]

    pidor_message = get_random_file(pidor_messages, {})

    for text in pidor_message["intro_messages"]:
        if text == "send_intro_sticker":
            bot.send_sticker(chat.id, intro_stickers.get_random()["file_id"])
        else:
            bot.send_message(chat.id, text, parse_mode=pidor_message["parse_mode"])
        sleep(pidor_message["sleep_time"])

    if not cheated_participants:
        winner = choice(participants)
    else:
        winner = choice(cheated_participants)

    chats.update_one({"chat_id": chat.id, "personal_id": winner.user.id}, {"$inc": {"score": 1}})
    bot.send_message(chat.id, pidor_message["winner_message"].format(user_system.get_username(winner.user, chat)),
                     parse_mode=pidor_message["parse_mode"])

    timings.update_one({"chat_id": chat.id, "game": "pidor"}, {"$set": {"pidor_of_the_day": winner.user.id}})

    sleep(pidor_message["sleep_time"])

    personal_sticker = personal_stickers.get_random(winner.user)
    if personal_sticker is not None:
        bot.send_sticker(chat.id, personal_stickers.get_random(winner.user)["file_id"])


@bot.message_handler(commands=["piu"])
def echo_piu(message):
    piu_messages = db.get_instance()["piuMessages"]
    chats = db.get_instance()["chats"]
    chat = message.chat
    sender = message.from_user

    if timings.find_one({"chat_id": chat.id, "game": "piu", "personal_id": sender.id}) is None:
        timings.insert_one(
            {"game": "piu", "chat_id": chat.id, "personal_id": sender.id, "last_run": None, "delta_hours": 0,
             "delta_minutes": 10, "label_hours": ["час", "часа", "часов"],
             "label_minutes": ["минуту", "минуты", "минут"], "label_seconds": ["секунду", "секунды", "секунд"]})

    timing = timings.find_one({"chat_id": chat.id, "personal_id": sender.id, "game": "piu"})
    current_date = datetime.datetime.now()

    if timing["last_run"] is None:
        timings.update_one({"chat_id": chat.id, "personal_id": sender.id, "game": "piu"},
                           {"$set": {"last_run": date_to_tuple(current_date)}})
    else:
        last_run = datetime.datetime(*timing["last_run"])
        delta = datetime.timedelta(hours=timing["delta_hours"], minutes=timing["delta_minutes"])

        if last_run + delta > current_date:
            answer = answers.get(Context.still_early_piu)
            bot.send_message(chat.id, answer.message.format(
                date_representation(last_run + delta - current_date, timing)), parse_mode=answer.parse_mode)
            return
        else:
            timings.update_one({"chat_id": chat.id, "personal_id": sender.id, "game": "piu"},
                               {"$set": {"last_run": date_to_tuple(current_date)}})

    piu_message = get_random_file(piu_messages, {})
    sending_message, parse_mode = piu_message["message"], piu_message["parse_mode"]

    receiver = message.text.split()[1] if len(message.text.split()) > 1 else sender.username
    bot.send_message(chat.id, sending_message.format(user_system.get_username(sender, chat), receiver),
                     parse_mode=parse_mode)

    personal_sticker = personal_stickers.get_random(sender)
    if personal_sticker is not None:
        sleep(piu_message["sleep_time"])
        bot.send_sticker(chat.id, personal_stickers.get_random(sender)["file_id"])

    if receiver != sender.username:
        chats.update_one({"chat_id": chat.id, "personal_id": sender.id}, {"$inc": {"piu_count": 1}})


@bot.message_handler(commands=["pua"])
def echo_pua(message):
    pua_messages = db.get_instance()["puaMessages"]
    chats = db.get_instance()["chats"]
    chat = message.chat
    sender = message.from_user

    if timings.find_one({"chat_id": chat.id, "game": "pua", "personal_id": sender.id}) is None:
        timings.insert_one(
            {"game": "pua", "chat_id": chat.id, "personal_id": sender.id, "last_run": None, "delta_hours": 0,
             "delta_minutes": 5, "label_hours": ["час", "часа", "часов"],
             "label_minutes": ["минуту", "минуты", "минут"], "label_seconds": ["секунду", "секунды", "секунд"]})

    timing = timings.find_one({"chat_id": chat.id, "personal_id": sender.id, "game": "pua"})
    current_date = datetime.datetime.now()

    if timing["last_run"] is None:
        timings.update_one({"chat_id": chat.id, "personal_id": sender.id, "game": "pua"},
                           {"$set": {"last_run": date_to_tuple(current_date)}})
    else:
        last_run = datetime.datetime(*timing["last_run"])
        delta = datetime.timedelta(hours=timing["delta_hours"], minutes=timing["delta_minutes"])

        if last_run + delta > current_date:
            answer = answers.get(Context.still_early_pua)
            bot.send_message(chat.id, answer.message.format(
                date_representation(last_run + delta - current_date, timing)), parse_mode=answer.parse_mode)
            return
        else:
            timings.update_one({"chat_id": chat.id, "personal_id": sender.id, "game": "pua"},
                               {"$set": {"last_run": date_to_tuple(current_date)}})

    pua_message = get_random_file(pua_messages, {})
    sending_message, parse_mode = pua_message["message"], pua_message["parse_mode"]

    bot.send_message(chat.id, sending_message.format(user_system.get_username(sender, chat)), parse_mode=parse_mode)

    chats.update_one({"chat_id": chat.id, "personal_id": sender.id}, {"$inc": {"pua_count": 1}})


@bot.message_handler(commands=["wink"])
def echo_wink(message):
    wink_messages = db.get_instance()["winkMessages"]
    chats = db.get_instance()["chats"]
    chat = message.chat
    sender = message.from_user

    if timings.find_one({"chat_id": chat.id, "game": "wink", "personal_id": sender.id}) is None:
        timings.insert_one(
            {"game": "wink", "chat_id": chat.id, "personal_id": sender.id, "last_run": None, "delta_hours": 0,
             "delta_minutes": 7, "label_hours": ["час", "часа", "часов"],
             "label_minutes": ["минуту", "минуты", "минут"], "label_seconds": ["секунду", "секунды", "секунд"]})

    if wink_messages.find_one({"context": "last_wink", "chat_id": chat.id}) is None:
        wink_messages.insert_one(
            {"context": "last_wink", "chat_id": chat.id, "status": False, "personal_id": None, "last_wink": None,
             "delta_minutes": 1})

    current_date = datetime.datetime.now()
    last_wink = wink_messages.find_one({"context": "last_wink", "chat_id": chat.id})
    if last_wink["status"] and (last_wink["personal_id"] != sender.id):
        delta = datetime.timedelta(minutes=last_wink["delta_minutes"])
        if datetime.datetime(*last_wink["last_wink"]) + delta > current_date:
            wink_message = get_random_file(wink_messages, {"type": "multi"})
            sending_message, parse_mode = wink_message["message"], wink_message["parse_mode"]
            bot.send_message(chat.id, sending_message.format(
                user_system.get_username(bot.get_chat_member(chat.id, last_wink["personal_id"]).user, chat),
                user_system.get_username(sender, chat)), parse_mode=parse_mode)

            for pers_id in [sender.id, last_wink["personal_id"]]:
                chats.update_one({"chat_id": chat.id, "personal_id": pers_id}, {"$inc": {"wink_count": 1}})

            wink_messages.update_one({"context": "last_wink", "chat_id": chat.id}, {"$set": {"status": False}})
            return
        else:
            wink_messages.update_one({"context": "last_wink", "chat_id": chat.id}, {"$set": {"status": False}})

    timing = timings.find_one({"chat_id": chat.id, "personal_id": sender.id, "game": "wink"})

    if timing["last_run"] is None:
        timings.update_one({"chat_id": chat.id, "personal_id": sender.id, "game": "wink"},
                           {"$set": {"last_run": date_to_tuple(current_date)}})
    else:
        last_run = datetime.datetime(*timing["last_run"])
        delta = datetime.timedelta(hours=timing["delta_hours"], minutes=timing["delta_minutes"])

        if last_run + delta > current_date:
            answer = answers.get(Context.still_early_wink)
            bot.send_message(chat.id, answer.message.format(
                date_representation(last_run + delta - current_date, timing)), parse_mode=answer.parse_mode)
            return
        else:
            timings.update_one({"chat_id": chat.id, "personal_id": sender.id, "game": "wink"},
                               {"$set": {"last_run": date_to_tuple(current_date)}})

    wink_message = get_random_file(wink_messages, {"type": "single"})
    sending_message, parse_mode = wink_message["message"], wink_message["parse_mode"]
    wink_messages.update_one({"context": "last_wink", "chat_id": chat.id}, {
        "$set": {"status": True, "personal_id": sender.id, "last_wink": date_to_tuple(current_date)}})

    bot.send_message(chat.id, sending_message.format(user_system.get_username(sender, chat)), parse_mode=parse_mode)


@bot.message_handler(commands=["pidorstats"])
def echo_pidorstats(message):
    chats = db.get_instance()["chats"]
    chat = message.chat
    participants = [(i, participant["personal_id"], participant["score"]) for i, participant in
                    enumerate(chats.find({"chat_id": chat.id}).sort("score", DESCENDING))]

    if not participants:
        answer = answers.get(Context.no_one_is_registered)
        bot.send_message(chat.id, answer.message, parse_mode=answer.parse_mode)
        return

    stats_messages = db.get_instance()["statsMessages"]
    stats_message = get_random_file(stats_messages, {"game": "pidor"})

    stats_list = "\n".join(
        [stats_message["list_format"].format(i + 1,
                                             user_system.get_username(bot.get_chat_member(chat.id, personal_id).user,
                                                                      chat),
                                             score, declination_count(score, "раз", "раза", "раз"))
         for i, personal_id, score in participants])

    if len([1 for i, personal_id, score in participants if score == participants[0][2]]) > 1:
        conclusion = stats_message["draft"]
    else:
        conclusion = stats_message["congratulation"].format(
            user_system.get_username(bot.get_chat_member(chat.id, participants[0][1]).user, chat))

    bot.send_message(chat.id, stats_message["tab"].join((stats_message["message"], stats_list, conclusion)),
                     parse_mode=stats_message["parse_mode"])


@bot.message_handler(commands=["piustats"])
def echo_piustats(message):
    chats = db.get_instance()["chats"]
    chat = message.chat
    participants = [(i, participant["personal_id"], participant["piu_count"]) for i, participant in
                    enumerate(chats.find({"chat_id": chat.id}).sort("piu_count", DESCENDING))]

    if not participants:
        answer = answers.get(Context.no_one_is_registered)
        bot.send_message(chat.id, answer.message, parse_mode=answer.parse_mode)
        return

    stats_messages = db.get_instance()["statsMessages"]
    stats_message = get_random_file(stats_messages, {"game": "piu"})

    stats_list = "\n".join(
        [stats_message["list_format"].format(i + 1,
                                             user_system.get_username(bot.get_chat_member(chat.id, personal_id).user,
                                                                      chat),
                                             score)
         for i, personal_id, score in participants])

    if len([1 for i, personal_id, score in participants if score == participants[0][2]]) > 1:
        conclusion = stats_message["draft"]
    else:
        conclusion = stats_message["congratulation"].format(
            user_system.get_username(bot.get_chat_member(chat.id, participants[0][1]).user, chat))

    bot.send_message(chat.id, stats_message["tab"].join((stats_message["message"], stats_list, conclusion)),
                     parse_mode=stats_message["parse_mode"])


@bot.message_handler(commands=["puastats"])
def echo_puastats(message):
    chats = db.get_instance()["chats"]
    chat = message.chat
    participants = [(i, participant["personal_id"], participant["pua_count"]) for i, participant in
                    enumerate(chats.find({"chat_id": chat.id}).sort("pua_count", DESCENDING))]

    if not participants:
        answer = answers.get(Context.no_one_is_registered)
        bot.send_message(chat.id, answer.message, parse_mode=answer.parse_mode)
        return

    stats_messages = db.get_instance()["statsMessages"]
    stats_message = get_random_file(stats_messages, {"game": "pua"})

    stats_list = "\n".join(
        [stats_message["list_format"].format(i + 1,
                                             user_system.get_username(bot.get_chat_member(chat.id, personal_id).user,
                                                                      chat),
                                             score)
         for i, personal_id, score in participants])

    if len([1 for i, personal_id, score in participants if score == participants[0][2]]) > 1:
        conclusion = stats_message["draft"]
    else:
        conclusion = stats_message["congratulation"].format(
            user_system.get_username(bot.get_chat_member(chat.id, participants[0][1]).user, chat))

    bot.send_message(chat.id, stats_message["tab"].join((stats_message["message"], stats_list, conclusion)),
                     parse_mode=stats_message["parse_mode"])


@bot.message_handler(commands=["winkstats"])
def echo_winkstats(message):
    chats = db.get_instance()["chats"]
    chat = message.chat
    participants = [(i, participant["personal_id"], participant["wink_count"]) for i, participant in
                    enumerate(chats.find({"chat_id": chat.id}).sort("wink_count", DESCENDING))]

    if not participants:
        answer = answers.get(Context.no_one_is_registered)
        bot.send_message(chat.id, answer.message, parse_mode=answer.parse_mode)
        return

    stats_messages = db.get_instance()["statsMessages"]
    stats_message = get_random_file(stats_messages, {"game": "wink"})

    stats_list = "\n".join(
        [stats_message["list_format"].format(i + 1,
                                             user_system.get_username(bot.get_chat_member(chat.id, personal_id).user,
                                                                      chat),
                                             score, declination_count(score, "раз", "раза", "раз"))
         for i, personal_id, score in participants])

    leaders = [user_system.get_username(bot.get_chat_member(chat.id, personal_id).user, chat) for
               i, personal_id, score in participants if score == participants[0][2]]

    if participants[0][2] == 0:
        conclusion = stats_message["draft"]
    elif len(leaders) == 1:
        conclusion = stats_message["congratulation_one"].format(", ".join(leaders))
    else:
        conclusion = stats_message["congratulation_many"].format(", ".join(leaders))

    bot.send_message(chat.id, stats_message["tab"].join((stats_message["message"], stats_list, conclusion)),
                     parse_mode=stats_message["parse_mode"])


@bot.message_handler(commands=["dice"])
def echo_dice(message):
    dices = ["🎲", "🎯", "🏀"]
    bot.send_dice(message.chat.id, emoji=choice(dices))


@bot.message_handler(commands=["durka"])
def echo_durka(message):
    bot.send_message(message.chat.id, "🚑")


@bot.message_handler(commands=["readpersonalstickers"])
def echo_readpersonalstickers(message):
    chats = db.get_instance()["chats"]
    chat = message.chat
    sender = message.from_user

    if sender.id != chat.id:
        answer = answers.get(Context.reading_stickers_in_conversation)
        bot.reply_to(message, answer.message, parse_mode=answer.parse_mode)
        return

    if chats.find_one({"personal_id": sender.id, "chat_id": chat.id}) is None:
        answer = answers.get(Context.not_registered)
        bot.send_message(chat.id, answer.message, answer.parse_mode)
        return

    if chats.find_one({"chat_id": chat.id, "personal_id": sender.id})["sticker_reading_mode"]:
        chats.update_one({"chat_id": chat.id, "personal_id": sender.id}, {"$set": {"sticker_reading_mode": False}})
        answer = answers.get(Context.end_of_reading_stickers)
        bot.send_message(chat.id, answer.message, parse_mode=answer.parse_mode)
        return

    answer = answers.get(Context.start_reading_stickers)
    bot.send_message(chat.id, answer.message, parse_mode=answer.parse_mode)

    chats.update_one({"chat_id": chat.id, "personal_id": sender.id}, {"$set": {"sticker_reading_mode": True}})


@bot.message_handler(commands=["setemoji"])
def echo_setemoji(message):
    chats = db.get_instance()["chats"]
    chat = message.chat
    sender = message.from_user

    personal_emoji = text_has_emoji(message.text)
    if personal_emoji is None:
        return
    chats.update_many({"personal_id": sender.id}, {"$set": {"emoji": personal_emoji}})

    answer = answers.get(Context.emoji_supplied)
    bot.send_message(chat.id, answer.message, parse_mode=answer.parse_mode)


@bot.message_handler(content_types=["sticker"])
def echo_sticker(message):
    personal_stickers = db.get_instance()["personalStickers"]
    chats = db.get_instance()["chats"]
    sticker = message.sticker
    chat = message.chat
    sender = message.from_user

    if chat.id != sender.id:
        return

    if not chats.find_one({"chat_id": chat.id, "personal_id": sender.id})["sticker_reading_mode"]:
        return

    if personal_stickers.find_one(
            {"personal_id": sender.id, "set_name": sticker.set_name, "emoji": sticker.emoji}) is None:
        personal_stickers.insert_one(
            {"personal_id": sender.id, "file_id": sticker.file_id, "set_name": sticker.set_name,
             "emoji": sticker.emoji})
        result = Context.sticker_was_added_successfully
    else:
        result = Context.sticker_has_already_been_added

    answer = answers.get(result)
    bot.send_message(chat.id, answer.message, parse_mode=answer.parse_mode)


bot.polling()
