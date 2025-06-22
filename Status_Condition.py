import random

def Status_condition_effect(Pokemon):
    if Pokemon.Status_condition == "Paralyzed":
        dice = random.randint(1, 100)
        if dice <= 25:
            print("You got Stephen Hawkins'ed")
            return True
        else:
            return False
    
    elif Pokemon.Status_condition == "Poisoned":
        damage = (1/8)*(Pokemon.Stats["hp"])
        Pokemon.HP -= damage
        print(f"{Pokemon.name} took {damage} damage from Poison")
