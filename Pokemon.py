# from Pokemon_data.Move_lister import Get_Pokemon_info
import asyncio
from Move_lister_async import Get_Pokemon_info
from Move_lister_async import move_retreiver
# from Pokemon_data.Move_lister import move_retreiver
from Pokemon_data.Ability_lister import ability_list
from Pokemon_data.Stats_lister import stat_lister
from Pokemon_data.Type_lister import type_lister
from Pokemon_Data_Retriever_Utilities.exp import Growth_rate
class Pokemon:
    
    def __init__(self, Name, level = 5):
        self.Pokemon_info = Get_Pokemon_info(Name)
        self.exp = 0
        self.level = level
        self.name = self.Pokemon_info["name"]
        self.level_up_exp = Growth_rate(self.name, self.level) 
        self.exp_death = (self.Pokemon_info["base_experience"] * 1.5 * self.level)//7
        self.moveset, self.moves, self.level_storage = asyncio.run(move_retreiver(self.name, self.level))
        # self.moveset, self.moves, self.level_storage = move_retreiver(self.name, self.level)
        self.Ability, self.status = ability_list(self.Pokemon_info)
        self.Stats = stat_lister(self.Pokemon_info)
        self.Typing = type_lister(self.Pokemon_info)
        self.Status_condition = None
        self.life = "Alive"
    def separate(self):
        self.info = open("Pokemon_info", "a")
        for i,j in self.Pokemon_info.items():
            self.info.write(i)
            self.info.write(f"{j}")
            self.info.write("\n")
    def level_up(self):
        self.level += 1
        self.level_up_exp = Growth_rate(self.name, self.level)
        print(self.level)
        print(self.level_storage[self.level])
        if self.level_storage[self.level]:
            for i in self.level_storage[self.level]:
                while True:
                    print(f"Your Pokemon wants to learn {i}")
                    player_response =  input("Do you want to teach it?\nY/N\n")
                    if player_response == "Y":
                        print("Which move do you want to replace?")
                    count = 1
                    for j in self.moveset.keys():
                        print(f"{count}.{j}", end = " ")
                        count += 1
                    response = input("\n")
                    move = list(self.moveset.keys())
                    ans = input(f"Are you sure you want to replace {move[int(response)-1]}\n")
                    if ans.lower() == "yes":
                        del self.moveset[move[int(response)-1]]
                        self.moveset[i] = self.moves[i]
                        break
                    else:
                        continue
