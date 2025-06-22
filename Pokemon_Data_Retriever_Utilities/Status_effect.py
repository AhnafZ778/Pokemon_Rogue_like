def Status_effect(effect, Pokemon = None):
    if effect == "paralysis":
        print("Congrats you're practically Stephen Hawkins now")
        return "Paralyzed"
    elif effect == "burn":
        print("Bro is the Human Torch now")
        Pokemon.Stats["attack"] /= 2
        return "Burned"
    elif effect == "freeze":
        print("LET IT MOTHERFUCKING GO AHH SPELL")
        return "Frozen"
    elif effect == "poison":
        print("Pfft someone got nom nommed by a python")
        return "Poisoned"
    elif effect == "sleep":
        print("Bro fell asleep at the job")
        return "Sleep"
