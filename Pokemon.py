from Pokemon_data.Move_lister import Get_Pokemon_info
from Pokemon_data.Move_lister import move_retreiver
from Pokemon_data.Ability_lister import ability_list
from Pokemon_data.Stats_lister import stat_lister
from Pokemon_data.Type_lister import type_lister

class Pokemon:
    def __init__(self, Name):
        self.name = Name
        self.Pokemon_info = Get_Pokemon_info(self.name)
        self.moveset, self.moves = move_retreiver(self.name)
        self.Ability, self.status = ability_list(self.Pokemon_info)
        self.Stats = stat_lister(self.Pokemon_info)
        self.Typing = type_lister(self.Pokemon_info)
    def separate(self):
        self.Abilities = open("Pokemon_data/Pokemon abilities.py", "a", encoding= "UTF-8")
        self.Types = open("Pokemon_data/Pokemon Types.py", "a", encoding= "UTF-8")
        self.Stats = open("Pokemon_data/Pokemon Stats.py", "a", encoding= "UTF-8")
        for i in self.Pokemon_info:
            if i == "abilities":
                self.Abilities.write(f"{self.Pokemon_info[i]}")
                self.Abilities.write("\n")
            elif i == "moves":
                self.Moves.write(f"{self.Pokemon_info[i]}")
                self.Moves.write("\n")
            elif i == "types":
                self.Types.write(f"{self.Pokemon_info[i]}")
                self.Types.write("\n")
            elif i == "stats":
                self.Stats.write(f"{self.Pokemon_info[i]}")
                self.Stats.write("\n")
    def level_up(self):
        self.level += 1
        self.level_up_exp = Growth_rate(self.name, self.level)
        print(self.level)
        print(self.level_storage[self.level])
        if self.level_storage[self.level]:
            for i in self.level_storage[self.level]:
                print(f"Your Pokemon wants to learn {i}")
                player_response =  input("Do you want to teach it?\n Y/N")
                print(player_response)

    
# Pokemon_Name = input("Insert the name of your desired pokemon: \n")
# if Get_Pokemon_info(Pokemon_Name):
#     Pokemon_Name = Pokemon(Pokemon_Name)
# print(Ability, Stats, Typing)
