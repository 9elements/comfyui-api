import random

def generate_random_15_digit_number():
  return random.randint(10**14, 10**15 - 1)