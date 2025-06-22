import random

def Status_condition_effect(Pokemon):
    if Pokemon.Status_condition == "Paralyzed":
        dice = random.randint(1, 100)
        if dice <= 25:
            print("You got Stephen Hawkins'ed")
            return True
        else:
            return False
    
