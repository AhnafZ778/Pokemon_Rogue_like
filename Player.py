from pokemon import Pokemon
import uuid
from Utilities.starting_screen import Starter_selection
import random

class Player:
    
    def __init__(self, Name):
        self.name = Name
        self.player_ID = uuid.uuid4()
        self.Alive_Pokemons = [Pokemon("budew")]
        self.Dead_Pokemons = []
        self.items = {}
        self.items["potion"] = 5
        self.items["antidote"] = 2
        self.items["freeze_heal"] = 0
        self.items["paralyze_heal"] = 0
        self.items["burn_heal"] = 0
        self.items["pokeballs"] = 10
        self.items["great_balls"] = 0
        self.items["revives"] = 3
        
    def give_Pokemons(self, num = 5):
        number = random.randint(1,num)
        for i in range(number):
            pokemon_ID = random.randint(1, 500)
            new_Pokemon = (Pokemon(pokemon_ID))
            self.Alive_Pokemons.append(new_Pokemon)
    
    def starter(self):
        Starter_selection()
        response = input("")
        if response == "1" or response.lower() == "charmander":
            print(f"{self.player_name} recieved Charmander the Fire type Pokemon!")
            charmander = Pokemon("Charmander")             
            self.Alive_Pokemons.append(charmander)
        elif response == "2" or response.lower() == "charmander":
            print(f"{self.player_name} recieved Bulbasaur the Grass type Pokemon!")
            bulbasaur = Pokemon("bulbasaur")             
            self.Alive_Pokemons.append(bulbasaur)
        elif response == "3" or response.lower() == "squirtle":
            print(f"{self.player_name} recieved Squirtle the Water type Pokemon!")
            squirtle = Pokemon("squirtle")             
            self.Alive_Pokemons.append(squirtle)
