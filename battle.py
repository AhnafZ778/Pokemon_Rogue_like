from Player import Player
from Trainer import Trainer
class Battle:
    
    def __init__(self, Player_1, Player_2):
        self.Player = Player(Player_1)
        self.Trainer = Player(Player_2)
        self.Player_Curr = self.Player.Alive_Pokemons.pop(0)
        self.Trainer_Curr = self.Trainer.Alive_Pokemons.pop(0)
    def Switch_Pokemons(self, Player):
        print("Which Pokemon Do you want to Switch into?")
        count = 1
        for i in Player.Alive_Pokemons:
            print(f"{count}. {i.name}", end = " ")
            count += 1
        while True:
            number = int(input("\n"))
            if number <= len(Player.Alive_Pokemons):
                Player.Alive_Pokemons.append(self.Player_Curr)
                self.Player_Curr = Player.Alive_Pokemons[number-1]
                print(self.Player_Curr.name)
                break
            else:
                print("No Pokemon at the Chosen Position")
                print("Please Pick Again.")
                
    def Use_item(self, pokemon, player):
        print(f"Which Item would you like to use on {pokemon.name}")
        avail = []
        for i,j in player.items.items():
            if j != 0:
                avail.append(i)
        for i in range(len(avail)):
            print(f"{i+1}. {avail[i]}: {player.items[avail[i]]}", end = " ")
        res = input("\n")
        response = int(res) - 1
        player.items[avail[response]] -= 1
