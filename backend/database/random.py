import random

def random_string(site_ids):
    number = random.randint(10000, 99999)
    while number in site_ids:
        number = random.randint(10000, 99999)
    return number