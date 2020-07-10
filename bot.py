from pymongo import MongoClient, DESCENDING
from os import environ
from random import choice
from time import sleep

from utils.utils import declination_count, get_random_file

import telebot

# with open("token.txt", "r") as tk:
#     TOKEN = tk.readline()

# with open("mongodb_url.txt", "r") as tk:
#     MONGODB_TOKEN = tk.readline().rstrip()


TOKEN = environ["TOKEN"]

MONGO_USERNAME = environ["MONGO_USERNAME"]
MONGO_PASSWORD = environ["MONGO_PASSWORD"]
MONGO_DB = environ["MONGO_DB"]

with open("mongodb_url.txt", "r") as tk:
    MONGODB_TOKEN = tk.readline().format(MONGO_USERNAME, MONGO_PASSWORD, MONGO_DB).rstrip()


def get_standard_answer(context):
    res = get_random_file(standard_answers, {"context": context})
    return res["message"], res["parse_mode"]


def get_random_intro_sticker():
    intro_stickers = dbase["introStickers"]
    return get_random_file(intro_stickers, {})


def get_random_personal_sticker(user):
    personal_stickers = dbase["personalStickers"]
    if personal_stickers.find_one({"personal_id": user.id}) is None:
        return None
    return get_random_file(personal_stickers, {"personal_id": user.id})


def add_new_player(user, chat):
    chats = dbase["chats"]

    current_user = chats.find_one({"personal_id": user.id, "chat_id": chat.id})

    if current_user is not None:
        return False
    chats.insert_one(
        {"personal_id": user.id, "chat_id": chat.id, "score": 0, "sticker_reading_mode": False, "piu_count": 0,
         "pua_count": 0, "wink_count": 0})
    return True


MONGO_DB = "BloodWhoresData"

bot = telebot.TeleBot(TOKEN)

cluster = MongoClient(MONGODB_TOKEN)
dbase = cluster[MONGO_DB]
standard_answers = dbase["standardAnswers"]


@bot.message_handler(commands=["register"])
def echo_register(message):
    chat = message.chat
    sender = message.from_user

    if add_new_player(sender, chat):
        result = "successful_registration"
    else:
        result = "already_registered"

    sending_message, parse_mode = get_standard_answer(result)
    bot.send_message(chat.id, sending_message.format(sender.username), parse_mode=parse_mode)


@bot.message_handler(commands=["pidor"])
def echo_pidor(message):
    chats = dbase["chats"]
    chat = message.chat
    participants = [bot.get_chat_member(chat.id, participant["personal_id"]) for participant in
                    chats.find({"chat_id": chat.id})]

    if len(participants) <= 0:
        sending_message, parse_mode = get_standard_answer("not_enough_players")
        bot.send_message(chat.id, sending_message, parse_mode=parse_mode)
    else:
        pidor_messages = dbase["pidorMessages"]

        pidor_message = get_random_file(pidor_messages, {})

        for text in pidor_message["intro_messages"]:
            if text == "send_intro_sticker":
                bot.send_sticker(chat.id, get_random_intro_sticker()["file_id"])
            else:
                bot.send_message(chat.id, text, parse_mode=pidor_message["parse_mode"])
            sleep(pidor_message["sleep_time"])

        winner = choice(participants)

        chats.update_one({"chat_id": chat.id, "personal_id": winner.user.id}, {"$inc": {"score": 1}})
        bot.send_message(chat.id, pidor_message["winner_message"].format(winner.user.username),
                         parse_mode=pidor_message["parse_mode"])

        sleep(pidor_message["sleep_time"])

        personal_sticker = get_random_personal_sticker(winner.user)
        if personal_sticker is not None:
            bot.send_sticker(chat.id, get_random_personal_sticker(winner.user)["file_id"])


@bot.message_handler(commands=["pidorstats"])
def echo_pidorstats(message):
    chats = dbase["chats"]
    chat = message.chat
    participants = [(i, participant["personal_id"], participant["score"]) for i, participant in
                    enumerate(chats.find({"chat_id": chat.id}).sort("score", DESCENDING))]

    if not participants:
        sending_message, parse_mode = get_standard_answer("no_one_is_registered")
        bot.send_message(chat.id, sending_message, parse_mode=parse_mode)
        return

    stats_messages = dbase["statsMessages"]
    stats_message = get_random_file(stats_messages, {"game": "pidor"})

    stats_list = "\n".join(
        [stats_message["list_format"].format(i + 1, bot.get_chat_member(chat.id, personal_id).user.username, score,
                                             declination_count(score))
         for i, personal_id, score in participants])

    if len([1 for i, personal_id, score in participants if score == participants[0][2]]) > 1:
        conclusion = stats_message["draft"]
    else:
        conclusion = stats_message["congratulation"].format(
            bot.get_chat_member(chat.id, participants[0][1]).user.username)

    bot.send_message(chat.id, stats_message["tab"].join((stats_message["message"], stats_list, conclusion)),
                     parse_mode=stats_message["parse_mode"])


@bot.message_handler(commands=["piustats"])
def echo_piustats(message):
    chats = dbase["chats"]
    chat = message.chat
    participants = [(i, participant["personal_id"], participant["piu_count"]) for i, participant in
                    enumerate(chats.find({"chat_id": chat.id}).sort("piu_count", DESCENDING))]

    if not participants:
        sending_message, parse_mode = get_standard_answer("no_one_is_registered")
        bot.send_message(chat.id, sending_message, parse_mode=parse_mode)
        return

    stats_messages = dbase["statsMessages"]
    stats_message = get_random_file(stats_messages, {"game": "piu"})

    stats_list = "\n".join(
        [stats_message["list_format"].format(i + 1, bot.get_chat_member(chat.id, personal_id).user.username, score,
                                             declination_count(score))
         for i, personal_id, score in participants])

    if len([1 for i, personal_id, score in participants if score == participants[0][2]]) > 1:
        conclusion = stats_message["draft"]
    else:
        conclusion = stats_message["congratulation"].format(
            bot.get_chat_member(chat.id, participants[0][1]).user.username)

    bot.send_message(chat.id, stats_message["tab"].join((stats_message["message"], stats_list, conclusion)),
                     parse_mode=stats_message["parse_mode"])


@bot.message_handler(commands=["readpersonalstickers"])
def echo_readpersonalstickers(message):
    chats = dbase["chats"]
    chat = message.chat
    sender = message.from_user

    if sender.id != chat.id:
        sending_message, parse_mode = get_standard_answer("reading_stickers_in_conversation")
        bot.reply_to(message, sending_message, parse_mode=parse_mode)
        return

    if chats.find_one({"personal_id": sender.id, "chat_id": chat.id}) is None:
        sending_message, parse_mode = get_standard_answer("not_registered")
        bot.send_message(chat.id, sending_message, parse_mode)
        return

    if chats.find_one({"chat_id": chat.id, "personal_id": sender.id})["sticker_reading_mode"]:
        chats.update_one({"chat_id": chat.id, "personal_id": sender.id}, {"$set": {"sticker_reading_mode": False}})
        sending_message, parse_mode = get_standard_answer("end_of_reading_stickers")
        bot.send_message(chat.id, sending_message, parse_mode=parse_mode)
        return

    sending_message, parse_mode = get_standard_answer("start_reading_stickers")
    bot.send_message(chat.id, sending_message, parse_mode=parse_mode)

    chats.update_one({"chat_id": chat.id, "personal_id": sender.id}, {"$set": {"sticker_reading_mode": True}})


@bot.message_handler(commands=["piu"])
def echo_piu(message):
    piu_messages = dbase["piuMessages"]
    chats = dbase["chats"]
    chat = message.chat
    sender = message.from_user

    piu_message = get_random_file(piu_messages, {})
    sending_message, parse_mode = piu_message["message"], piu_message["parse_mode"]

    receiver = message.text.split()[1] if len(message.text.split()) > 1 else sender.username
    bot.send_message(chat.id, sending_message.format(sender.username, receiver), parse_mode=parse_mode)

    personal_sticker = get_random_personal_sticker(sender)
    if personal_sticker is not None:
        bot.send_sticker(chat.id, get_random_personal_sticker(sender)["file_id"])

    if receiver != sender.username:
        chats.update_one({"chat_id": chat.id, "personal_id": sender.id}, {"$inc": {"piu_count": 1}})


@bot.message_handler(content_types=["sticker"])
def echo_all(message):
    personal_stickers = dbase["personalStickers"]
    chats = dbase["chats"]
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
        result = "sticker_was_added_successfully"
    else:
        result = "sticker_has_already_been_added"

    sending_message, parse_mode = get_standard_answer(result)
    bot.send_message(chat.id, sending_message, parse_mode=parse_mode)


bot.polling()
