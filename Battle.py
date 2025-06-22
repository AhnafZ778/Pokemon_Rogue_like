import random
from Utilities.isCritical import isCritical
from Player import Player
from Random_Entity_Generator.Trainer import Trainer
from item_effects import effect
from Utilities.Status_effect import Status_effect
class Battle:

class Battle:
    
    def __init__(self, Player_1, Player_2):
        self.Player = Player_1
        self.Trainer = Player_2
        self.Player_Curr = self.Player.Alive_Pokemons.pop(0)
        print(type(self.Player_Curr))
        self.Trainer_Curr = self.Trainer.Alive_Pokemons.pop(0)

    def check_match(self):
        if not self.Player.Alive_Pokemons and self.Player_Curr.HP <= 0:
            print("You Lost")
            return True
        elif not self.Trainer.Alive_Pokemons and self.Trainer_Curr.HP <= 0:
            print("You Win")
            return True
        else:
            return False
        
    def Switch_Pokemons(self, Player):
        count = 1
        if Player != self.Trainer:
            print("Which Pokemon Do you want to Switch into?")
            for i in Player.Alive_Pokemons:
                print(f"{count}. {i.name.capitalize()}", end = " ")
                count += 1
            while True:
                number = int(input("\n"))
                number -= 1
                if number <= len(Player.Alive_Pokemons):
                    if self.Player_Curr not in self.Player.Dead_Pokemons:
                        Player.Alive_Pokemons.append(self.Player_Curr)
                    self.Player_Curr = (Player.Alive_Pokemons.pop(number))
                    print(f"You sent out {self.Player_Curr.name.capitalize()}")
                    break
                else:
                    print("No Pokemon at the Chosen Position")
                    print("Please Pick Again.")
        else:
            poke_choice = random.randint(0, len(self.Trainer.Alive_Pokemons)-1)
            if self.Trainer_Curr not in self.Trainer.Dead_Pokemons:
                Player.Alive_Pokemons.append(self.Trainer_Curr)
            self.Trainer_Curr = Player.Alive_Pokemons.pop([poke_choice-1])
            print(f"{self.Trainer.name} sent out {self.Trainer_Curr.name.capitalize()}")
            
                
    def Use_item(self, pokemon, player):
        print(f"Which Item would you like to use on {pokemon.name.capitalize()}")
        avail = []
        for i,j in player.items.items():
            if j != 0:
                avail.append(i)
        for i in range(len(avail)):
            print(f"{i+1}. {avail[i]}: {player.items[avail[i]]}", end = " ")
        res = input("\n")
        response = int(res) - 1
        player.items[avail[response]] -= 1
        
    def Attack(self, pokemon):
        # print(pokemon.name)
        # print(pokemon.moveset)
        # print(pokemon.moves)
        print("What Move would you like to use?")
        count = 1
        for i,j in pokemon.moveset.items():
            print(f"{count}. {i}", end = " ")
            count += 1
        response = int(input("\n"))
        moves = list(pokemon.moveset.keys())
        res_move = moves[response-1]
        print(f"{pokemon.name.capitalize()} Used {res_move} on {self.Trainer.name.capitalize()}'s {self.Trainer_Curr.name.capitalize()}")
        # print(pokemon.moveset[res_move]["Power"])
        Power = pokemon.moveset[res_move]["Power"]
        if Power:
            crit = isCritical()
            cri = False
            if crit:
                Critical = 1.5
                cri = True
            else:
                Critical = 1
            A = pokemon.Stats["attack"]
            D = self.Trainer_Curr.Stats["defense"]
            damage = (((2 * pokemon.level * Critical / 5 + 2) * Power * (A / D)) / 50) + 2
            damage = round(damage, 2)
            if damage > 0:
                self.Trainer_Curr.HP -= damage
                self.Trainer_Curr.HP = round(self.Trainer_Curr.HP, 2)
                print(f"It caused {damage} damage on {self.Trainer_Curr.name.capitalize()}")
                if cri:
                    print("It's a Critical Hit!!")
            if self.Trainer_Curr.HP <= 0:
                print(f"{self.Trainer_Curr.name.capitalize()} has fainted.")
                dead = self.Trainer_Curr
                self.Trainer.Dead_Pokemons.append(dead)
                res = self.check_match()
                if res:
                    return True
                else:
                    self.Switch_Pokemons(self.Trainer)
            else:
                print(f"{self.Trainer_Curr.name.capitalize()} has {self.Trainer_Curr.HP} HP remaining")
        else:
            print("OK")
            if (pokemon.moveset[res_move]["Status_changes"]):
                print("OK^2")
                for i,j in pokemon.moveset[res_move]["Status_changes"].items():
                    print(i)
                    if i == "attack":
                        if j > 0:
                            print(self.Player_Curr.Stats["attack"])
                            self.Player_Curr.Stats["attack"] += self.Player_Curr.Stats["attack"]*(0.5 * j)
                            print(self.Player_Curr.Stats["attack"])
                        else:
                            print(self.Trainer_Curr.Stats["attack"])
                            self.Trainer_Curr.Stats["attack"] += self.Trainer_Curr.Stats["attack"]*(0.5 * j)
                            print(self.Trainer_Curr.Stats["attack"])
                    elif i == "defense":
                        if j > 0:
                            print(self.Player_Curr.Stats["defense"])
                            self.Player_Curr.Stats["defense"] += self.Player_Curr.Stats["defense"]*(0.5 * j)
                            print(self.Player_Curr.Stats["defense"])
                        else:
                            print(self.Trainer_Curr.Stats["defense"])
                            self.Trainer_Curr.Stats["defense"] += self.Trainer_Curr.Stats["defense"]*(0.5 * j)
                            print(self.Trainer_Curr.Stats["defense"])
                    elif i in self.statuses:
                    if not self.Trainer_Curr.Status_condition:
                        rng = random.randint(1, 100)
                        if rng <= j:
                            self.Trainer_Curr.Status_condition = Status_effect(i)
                    else:
                        print("Bro already disabled bruh chill")
                        
                    
            
            
        # print((res_move.keys()))
        
    def Player_turn(self):
        print("What would you like to do?")
        print("1. Attack 2. Switch Pokemons 3. Use Items")
        response = int(input(""))
        match = None
        if response == 1:
            match = self.Attack(self.Player_Curr)
        elif response == 2:
            self.Switch_Pokemons(self.Player)
        elif response == 3:
            self.Use_item(self.Player_Curr, self.Player)
        return match
    
    
    
    def Trainer_turn(self):
        if 0 < self.Trainer_Curr.HP < self.Trainer_Curr.HP * 0.2:
            self.Trainer.items["potions"] -= 1
            print(f"{self.Trainer.name.capitalize()} used Potion on {self.Trainer_Curr.name.capitalize()}")
        else:
            damage = []
            for i in self.Trainer_Curr.moveset:
                if self.Trainer_Curr.moveset[i]["Power"]:
                    damage.append(i)
            if damage:
                choice = random.randint(0, len(damage)-1)
                print(f"{self.Trainer_Curr.name.capitalize()} used {damage[choice]}")
                Power = self.Trainer_Curr.moveset[damage[choice]]["Power"]
                crit = isCritical()
                cri = False
                Critical = 1
                if crit:
                    Critical = 1.5
                    cri = True
                A = self.Trainer_Curr.Stats["attack"]
                D = self.Player_Curr.Stats["defense"]
                damage = (((2 * self.Trainer_Curr.level * Critical / 5 + 2) * Power * (A / D)) / 50) + 2
                damage = round(damage, 2)
                self.Player_Curr.HP -= damage
                self.Player_Curr.HP = round(self.Player_Curr.HP, 2)
                print(f"It caused {damage} damage on {self.Player_Curr.name.capitalize()}")
                print(f"{self.Player_Curr.name.capitalize()} has {self.Player_Curr.HP} HP remaining")
                if cri:
                    print("It's a Critical Hit!!")
                if self.Player_Curr.HP <= 0:
                    print(f"Your {self.Player_Curr.name} has fainted.")
                    dead = self.Player_Curr
                    self.Player.Dead_Pokemons.append(dead)
                    # print(self.Player.Dead_Pokemons)
                    check = self.check_match()
                    if check:
                        return True
                    else:
                        self.Switch_Pokemons(self.Player)
            else:
                print("No damaging Moves, lol betacuck")
