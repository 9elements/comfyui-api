import random

def generate_random_15_digit_number():
    number = random.randint(10**14, 10**15 - 1)
    return number