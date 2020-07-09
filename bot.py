from pymongo import MongoClient, ASCENDING, DESCENDING
from emojis import face_with_cold_sweat, white_heavy_check_mark, cross_mark
from os import environ
from random import choice
from time import sleep

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


bot = telebot.TeleBot(TOKEN)

cluster = MongoClient(MONGODB_TOKEN)
dbase = cluster[MONGO_DB]


# @bot.message_handler(content_types=["sticker"])
# def echo_all(message):
#     intro_stickers = dbase["introStickers"]
#     sticker = message.sticker
#     intro_stickers.insert_one({"file_id": sticker.file_id})


def declination_count(num):
    if str(num)[-1] in "234":
        return "раза"
    return "раз"


@bot.message_handler(commands=["register"])
def echo_all(message):
    chats = dbase["chats"]
    chat = message.chat
    sender = message.from_user
    my_user = chats.find_one({"personal_id": sender.id, "chat_id": chat.id})
    if my_user is None:
        chats.insert_one({"personal_id": sender.id, "chat_id": chat.id, "score": 0})
        bot.send_message(chat.id,
                         u"Игрок {} успешно зарегистрирован  {}".format(sender.username, white_heavy_check_mark))
    else:
        bot.send_message(chat.id, u"Игрок {} уже участвует в игре  {}".format(sender.username, cross_mark))


@bot.message_handler(commands=["pidor"])
def echo_all(message):
    chats = dbase["chats"]
    chat = message.chat
    participants = [bot.get_chat_member(chat.id, participant["personal_id"]) for participant in
                    chats.find({"chat_id": chat.id})]

    if len(participants) <= 0:
        bot.send_message(chat.id, u"Недостаточно игроков для запуска игры {}".format(face_with_cold_sweat))
    else:
        pidor_messages = dbase["pidorMessages"]
        intro_stickers = dbase["introStickers"]

        intro_messages, winner_message = choice(
            [(variant["intro_messages"], variant["winner_message"]) for variant in pidor_messages.find()])
        intro_sticker_id = choice([sticker["file_id"] for sticker in intro_stickers.find()])

        bot.send_sticker(chat.id, intro_sticker_id)

        sleep(2.6)

        for text in intro_messages:
            bot.send_message(chat.id, text, parse_mode="HTML")
            sleep(2.6)

        winner = choice(participants)

        chats.update_one({"chat_id": chat.id, "personal_id": winner.user.id}, {"$inc": {"score": 1}})
        bot.send_message(chat.id, winner_message.format(winner.user.username))


@bot.message_handler(commands=["pidorstats"])
def echo_all(message):
    chats = dbase["chats"]
    chat = message.chat
    participants = [(i, participant["personal_id"], participant["score"]) for i, participant in
                    enumerate(chats.find({"chat_id": chat.id}).sort("score", DESCENDING))]

    if not participants:
        bot.send_message(chat.id, "К сожалению, в игре *Pidor Of The Day* никто не зарегистрирован 😕 Вот пидоры!",
                         parse_mode="Markdown")
        return

    stats_messages = dbase["statsMessages"]
    stats_message = choice(list(stats_messages.find()))

    stats_list = "\n".join(
        ["{}. <b>{}</b> - {} {}".format(i + 1, bot.get_chat_member(chat.id, personal_id).user.username, score,
                                        declination_count(score))
         for i, personal_id, score in participants])

    if len([1 for i, personal_id, score in participants if score == participants[0][2]]) > 1:
        conclusion = stats_message["draft"]
    else:
        conclusion = stats_message["congratulation"].format(
            bot.get_chat_member(chat.id, participants[0][1]).user.username)

    bot.send_message(chat.id, "\n\n".join((stats_message["message"], stats_list, conclusion)), parse_mode="HTML")


bot.polling()
