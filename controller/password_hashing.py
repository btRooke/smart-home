import hashlib
import random
import string

def generate_salt(length=16):
    """
    random salt of 16 characters
    """

    return "".join([random.choice(string.ascii_letters + string.digits) for i in range(length)])

def hash_string(string_to_hash):
    h = hashlib.sha256(string_to_hash.encode("utf-8"))
    return h.hexdigest()
