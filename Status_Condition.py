import random

def Status_condition_effect(Pokemon):
    if Pokemon.Status_condition == "Paralyzed":
        dice = random.randint(1, 100)
        if dice <= 25:
            if Pokemon.Status_condition:
                print("Bro is already disabled dude chill")
                return True
            else:
                print("You got Stephen Hawkins'ed")
                return True
        else:
            return False
    elif Pokemon.Status_condition == "Poisoned":
        damage = (1/8)*(Pokemon.Stats["hp"])
        Pokemon.HP -= damage
        print(f"{Pokemon.name} took {damage} damage from Poison")
    elif Pokemon.Status_condition == "Frozen":
        dice = random.randint(1, 100)
        if dice <= 45:
            if Pokemon.Status_condition:
                print("Bro is already disabled dude chill")
                return True
            else:
                print("You're Still frozen my guy")
                return False
        else:
            print("Congrats you have officially let it go")
            Pokemon.Status_condition = None
            return True
        
    elif Pokemon.Status_condition == "Burned":
        damage = (1/16)*(Pokemon.Stats["hp"])
        Pokemon.HP -= damage
        print(f"{Pokemon.name} took {damage} damage from Burn")
        
        
    elif Pokemon.Status_condition == "Sleep":
        dice = random.randint(1, 100)
        if dice <= 45:
            if Pokemon.Status_condition:
                print("Bro is already disabled dude chill")
                return True
            else:
                print("Wake up you fucking sloth")
                return False
        else:
            print("Congrats you're no longer useless")
            Pokemon.Status_condition = None
            return False

    elif Pokemon.Status_condition == "Confused":
        global Confusion_count
        print(f"Your {Pokemon.name} is confused")
        dice = random.randint(1, 2)
        if dice == 1:
            Pokemon.confused = "Yes"
        else:
            Pokemon.confused = "No"
        Confusion_count += 1
        if Pokemon.confused == "No":
            if 4 - Confusion_count == 1:
                print(f"{Pokemon.name} broke out of confusion")
                Confusion_count = 0
                Pokemon.Status_condition = None
            else:
                dice = random.randint(1, (5 - Confusion_count))
                if dice == 1:
                    print(f"{Pokemon.name} broke out of confusion")
                    Confusion_count = 0
                    Pokemon.Status_condition = None
