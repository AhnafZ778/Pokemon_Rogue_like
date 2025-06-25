def effect(pokemon, item, trainer):
    if item == "potion":
        pokemon.HP += 20
        if pokemon.Stats["hp"] < pokemon.HP:
            pokemon.HP = pokemon.Stats["hp"]
    elif item == "antidote":
        if pokemon.Status_condition == "Poisoned":
            pokemon.Status_condition = None
            print(f"{pokemon.name}'s poison got healed")
        else:
            print("It had no effect")
    elif item == "paralyze_heal":
        if pokemon.Status_condition == "Paralyzed":
            pokemon.Status_condition = None
            print(f"{pokemon.name} is no longer paralyzed")
        else:
            print("It had no effect")
    elif item == "freeze_heal":
        if pokemon.Status_condition == "Frozen":
            pokemon.Status_condition = None
            print(f"{pokemon.name} is no longer frozen")
        else:
            print("It had no effect")
    elif item == "burn_heal":
        if pokemon.Status_condition == "Burned":
            pokemon.Status_condition = None
            print(f"{pokemon.name}'s burn got healed")
        else:
            print("It had no effect")
    elif item == "revives":
        if trainer.Dead_Pokemons:
            print("Which pokemon do you want to revive")
            count = 1
            for i in trainer.Dead_Pokemons:
                print(f"{count}. {i.name}")
                count += 1
            response = int(input("\n"))
            response -= 1
            res_pokemon = trainer.Dead_Pokemons[response]
            res_pokemon.life = "Alive"
            pokemon = trainer.Dead_Pokemons.pop(response)
            trainer.Alive_Pokemons.append(res_pokemon)
            res_pokemon.HP = res_pokemon.Stats["hp"]//2
            print(f"{res_pokemon.name} has risen from the dead")
        else:
            print("Pokemon is already alive you dimwit")
