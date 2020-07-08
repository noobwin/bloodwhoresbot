from pymongo import MongoClient
import telebot
import os

# with open("token.txt", "r") as tk:
#     TOKEN = tk.readline()

# with open("mongodb_url.txt", "r") as tk:
#     MONGODB_TOKEN = tk.readline().rstrip()

TOKEN = os.environ["TOKEN"]

MONGO_USERNAME = os.environ["MONGO_USERNAME"]
MONGO_PASSWORD = os.environ["MONGO_PASSWORD"]
MONGO_DB = os.environ["MONGO_DB"]
with open("mongodb_url.txt", "r") as tk:
    MONGODB_TOKEN = tk.readline().format(MONGO_USERNAME, MONGO_PASSWORD, MONGO_DB)


bot = telebot.TeleBot(TOKEN)

cluster = MongoClient(MONGODB_TOKEN)
db = cluster[MONGO_DB]
collection = db["chats"]


@bot.message_handler(func=lambda m: True)
def echo_all(message):
    chat = message.chat
    sender = message.from_user
    my_user = collection.find_one({"personal_id": sender.id, "chat_id": chat.id})
    if my_user is None:
        collection.insert_one({"personal_id": sender.id, "chat_id": chat.id, "score": 0})
        bot.send_message(chat.id, "Player {} registered successfully!".format(sender.username))
    else:
        bot.send_message(chat.id, "Player {} is already registered!".format(sender.username))


bot.polling()
