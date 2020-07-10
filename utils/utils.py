from random import choice


def declination_count(num):
    if 2 <= num % 10 <= 4 and not (12 <= num % 100 <= 14):
        return "раза"
    return "раз"


def get_random_file(collection, local_filter):
    return choice([file for file in collection.find(local_filter)])
