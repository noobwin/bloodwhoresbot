from random import choice
from emoji import UNICODE_EMOJI

import datetime


def declination_count(num, var1, var2, var3):
    if num % 10 == 1 and not (num % 100 == 11):
        return var1
    if 2 <= num % 10 <= 4 and not (12 <= num % 100 <= 14):
        return var2
    return var3


def get_random_file(collection, local_filter):
    return choice([file for file in collection.find(local_filter)])


def text_has_emoji(text):
    for character in text:
        if character in UNICODE_EMOJI:
            return character
    return None


def date_representation(date, labels):
    return " ".join(["{} {}".format(timing, declination_count(timing, var1, var2, var3)) for timing, var1, var2, var3 in
                     [(date.seconds // 3600, *labels["label_hours"]),
                      ((date.seconds // 60) % 60, *labels["label_minutes"]),
                      (date.seconds % 60, *labels["label_seconds"])] if timing])


def date_to_tuple(date):
    return tuple(map(int, date.strftime("%Y %m %d %H %M %S").split()))
