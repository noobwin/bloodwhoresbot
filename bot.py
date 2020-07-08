import telebot
import os

from paths import CHATS_PATH

with open("token.txt") as tk:
    TOKEN = tk.readline()

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(func=lambda m: True)
def echo_all(message):
    chat = message.chat
    sender = message.from_user
    current_chat_path = "{}/{}".format(CHATS_PATH, chat.id)
    players_path = "{}/players.txt".format(current_chat_path)

    if not os.path.isdir(current_chat_path):
        os.mkdir(current_chat_path)

    tmp = open(players_path, "a")
    tmp.close()

    with open(players_path, "r") as players_file:
        players = [int(line.rstrip()) for line in players_file]
    if sender.id not in players:
        with open("{}/players.txt".format(current_chat_path), "a") as players_file:
            print(sender.id, file=players_file)
        bot.send_message(chat.id, "Player {} registered successfully!".format(sender.username))
    else:
        bot.send_message(chat.id, "Player {} is already registered!".format(sender.username))


bot.polling()
