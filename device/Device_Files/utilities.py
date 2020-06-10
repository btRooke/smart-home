import random
import math
import os
import time

AUTH_KEY_FILE_NAME = "authentication_key.txt"
LOG_FILE = "log.txt"
KEY_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz123456789"

"""
ESP only has the random function getrandombits(n) where you get a random number
below or equal to the binary number with n bits. Therefore, functions need to be
written to get a random int and choice.
"""

# Recursion to figure out how many bits are needed to represent a base n number
def how_many_bits_to_represent(number, bits=1, base=2):
    if (base**bits - 1) // number:
        return bits
    else:
        return how_many_bits_to_represent(number, bits+1)

def randint(lower_bound, upper_bound):
    bits_needed = how_many_bits_to_represent(upper_bound - lower_bound)

    random.seed(time.ticks_cpu())
    random_number = random.getrandbits(bits_needed)

    while random_number > (upper_bound - lower_bound):
        random_number = random.getrandbits(bits_needed)

    return lower_bound + random_number

def random_choice(iterable):
    return iterable[randint(0, len(iterable) - 1)]

def read_file(filename):
    with open(filename, "r") as f:
        data = f.read()

    return data

def pretty_read_file(filename):
    data = read_file(filename)

    [print(line) for line in data.split("\n")]

def generate_auth_key_if_not_exists():
    if AUTH_KEY_FILE_NAME not in os.listdir():
        authentication_key = "".join([random_choice(KEY_ALPHABET) for i in range(32)])

        with open(AUTH_KEY_FILE_NAME, "w") as f:
            f.write(authentication_key)

def auth_key_is_valid(supplied_auth_key):
    auth_key = read_file(AUTH_KEY_FILE_NAME)
    return auth_key == supplied_auth_key

def merge_dicts(dict1, dict2):
    # If duplicate keys exist, dict1's key-value pair is used.

    for key in dict1.keys():
        dict2[key] = dict1[key]

    return dict2

def log(text):
    with open(LOG_FILE, "a") as f:
        f.write(text + "\n")
