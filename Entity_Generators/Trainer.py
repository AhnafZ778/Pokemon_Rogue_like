import uuid
import random
from pokemon import Pokemon
from names_generator import generate_name

class Trainer:
    
    def __init__(self):
        random_name = generate_name()
        first, last = random_name.split("_")
        self.name = last.capitalize()
        self.Alive_Pokemons = []
        self.Dead_Pokemons = []
        self.trainer_ID = uuid.uuid1()
        self.items = {}
        self.items["potion"] = 3
        self.items["antidote"] = 2
        self.items["freeze_heal"] = 0
        self.items["paralyze_heal"] = 0
        self.items["burn_heal"] = 0
        
    def give_Pokemons(self, num = 5):
        number = random.randint(1,num)
        self.Pokemons = []
        self.Pokemons_reference = []
        for i in range(number):
            pokemon_ID = random.randint(1, 500)
            new_Pokemon = (Pokemon(pokemon_ID))
            self.Alive_Pokemons.append(new_Pokemon)
