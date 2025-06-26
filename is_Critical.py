import random

def isCritical():
    number = random.randint(1, 100)
    if number <= 5:
        return True
    else:
        return False
