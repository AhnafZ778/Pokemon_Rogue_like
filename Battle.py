import random
from Utilities.isCritical import isCritical
from Player import Player
from Entity_Generators.Trainer import Trainer
from item_effects import effect
from Pokemon_Data_Retriever_Utilities.Status_effect import Status_effect
class Battle:
 
class Battle:
    
    def __init__(self, Player_1, Player_2):
        self.Player = Player_1
        self.Trainer = Player_2
        self.Player_Curr = self.Player.Alive_Pokemons.pop(0)
        print(type(self.Player_Curr))
        self.Trainer_Curr = self.Trainer.Alive_Pokemons.pop(0)
        self.statuses = ("paralysis", "freeze", "burn", "poison")

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
            poke_choice -= 1
            self.Trainer_Curr = Player.Alive_Pokemons.pop([poke_choice-1])
            print(f"{self.Trainer.name} sent out {self.Trainer_Curr.name.capitalize()}")
            
                
    def Use_item(self, pokemon, player, item = None):
        if not item:
            print(f"Which Item would you like to use on {pokemon.name.capitalize()}")
            avail = []
            for i,j in player.items.items():
                if j != 0:
                    avail.append(i)
            for i in range(len(avail)):
                print(f"{i+1}. {avail[i]}: {player.items[avail[i]]}", end = " ")
            res = input("\n")
            response = int(res) - 1
            effect(pokemon, avail[response], player)
            player.items[avail[response]] -= 1
        else:
            effect(pokemon, item, player)
            player.items[item] -= 1
        
    def Attack(self, pokemon):
        print("What Move would you like to use?")
        count = 1
        for i,j in pokemon.moveset.items():
            print(f"{count}. {i}", end = " ")
            count += 1
        response = int(input("\n"))
        moves = list(pokemon.moveset.keys())
        res_move = moves[response-1]
        print(f"{pokemon.name.capitalize()} Used {res_move} on {self.Trainer.name.capitalize()}'s {self.Trainer_Curr.name.capitalize()}")
        Power = pokemon.moveset[res_move]["Power"]
        matchup = asyncio.run(Matchup(pokemon.moveset[res_move]["Type_URL"]))
        multiplier = 1
        has_mul_1 = None
        has_mul_2 = None
        for i,j in matchup.items():
            if self.Trainer_Curr.Type_1 in j:
                has_mul_1 = i
            if self.Trainer_Curr.Type_2 in j:
                has_mul_2 = i
            
        has_mul_1 = self.convert_multipliers(has_mul_1)
        if self.Trainer_Curr.Type_2:
            has_mul_2 = self.convert_multipliers(has_mul_2)
        else:
            has_mul_2 = 1
        
        multiplier *= has_mul_1 * has_mul_2        
        if multiplier > 1:
            print("It's Super Effective!")
        if 0 < multiplier < 1:
            print("It's not Very Effective")
        
        if multiplier != 0:
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
                damage *= multiplier
                damage = round(damage, 2)
                if pokemon.Status_condition == "Confused":
                    Status_condition_effect(pokemon)
                    if pokemon.confused == "Yes":
                        pokemon.HP -= damage
                    if pokemon.HP <= 0:
                        print(f"Your {pokemon.name} has fainted.")
                        pokemon.life = "Dead"
                        dead = pokemon
                        self.Player.Dead_Pokemons.append(dead)
                        check = self.check_match()
                        if check:
                            return True
                        else:
                            self.Switch_Pokemons(self.Player)
                else:
                    if damage > 0:
                        self.Trainer_Curr.HP -= damage
                        self.Trainer_Curr.HP = round(self.Trainer_Curr.HP, 2)
                        print(f"It caused {damage} damage on {self.Trainer_Curr.name.capitalize()}")
                        if cri:
                            print("It's a Critical Hit!!")
                        if pokemon.moveset[res_move]["Life_drain"]:
                            print(f"It healed {pokemon.name} for {damage/2}")
                            pokemon.HP += (damage/2)
                            if pokemon.HP > pokemon.Stats["hp"]:
                                pokemon.HP = pokemon.Stats["hp"]
                    if self.Trainer_Curr.HP <= 0:
                        print(f"{self.Trainer_Curr.name.capitalize()} has fainted.")
                        dead = self.Trainer_Curr
                        self.Trainer_Curr.life = "Dead"
                        self.Trainer.Dead_Pokemons.append(dead)
                        res = self.check_match()
                        if res:
                            return True
                        else:
                            self.Switch_Pokemons(self.Trainer)
                            print("Do you want to switch Pokemons?")
                            switch_ask = int(input("1.Yes 2.No\n"))
                            if switch_ask == 1:
                                self.Switch_Pokemons(self.Player)
                            return "Switch"
                    else:
                        print(f"{self.Trainer_Curr.name.capitalize()} has {self.Trainer_Curr.HP} HP remaining")
            if (pokemon.moveset[res_move]["Status_changes"]):
                for i,j in pokemon.moveset[res_move]["Status_changes"].items():
                    # print(i, j)
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
                            # print(rng, j)
                            if rng <= j or j == 0:
                                self.Trainer_Curr.Status_condition = Status_effect(i, pokemon)
        else:
            print(f"{self.Trainer_Curr.name.capitalize()} is immune to {res_move}") 
                        
                    
            
            
        # print((res_move.keys()))
        
    def Player_turn(self):
        condition = True
        if self.Player_Curr.Status_condition == "Paralyzed" or self.Player_Curr.Status_condition == "Frozen" or self.Player_Curr.Status_condition == "Sleep":
            condition = Status_condition_effect(self.Player_Curr)
        if condition:
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
        if self.Player_Curr.Status_condition == "Poisoned" or self.Player_Curr.Status_condition == "Burned":
            Status_condition_effect(self.Player_Curr)
    
    
    
    def Trainer_turn(self):
        condition = True
        if self.Trainer_Curr.Status_condition == "Paralyzed" or self.Trainer_Curr.Status_condition == "Frozen" or self.Trainer_Curr.Status_condition == "Sleep":
            condition = Status_condition_effect(self.Player_Curr)
        if condition:
            if 0 < self.Trainer_Curr.HP < self.Trainer_Curr.HP * 0.2 and self.Trainer.items["potion"] > 0:
                self.Trainer.items["potion"] -= 1
                print(f"{self.Trainer.name.capitalize()} used Potion on {self.Trainer_Curr.name.capitalize()}")
            elif self.Trainer_Curr.Status_condition == "Paralyzed" and self.Trainer.items["paralyze_heal"] > 0:
                self.Use_item(self.Trainer_Curr, self.Trainer, "paralyze_heal")
            elif self.Trainer_Curr.Status_condition == "Frozen" and self.Trainer.items["freeze_heal"] > 0:
                self.Use_item(self.Trainer_Curr, self.Trainer, "freeze_heal")
            elif self.Trainer_Curr.Status_condition == "Burned" and self.Trainer.items["burn_heal"] > 0:
                self.Use_item(self.Trainer_Curr, self.Trainer, "burn_heal")
            elif self.Trainer_Curr.Status_condition == "Sleep" and self.Trainer.items["awakening"] > 0:
                self.Use_item(self.Trainer_Curr, self.Trainer, "awakening")
            elif self.Trainer_Curr.Status_condition == "Poisoned" and self.Trainer.items["antidote"] > 0:
                self.Use_item(self.Trainer_Curr, self.Trainer, "antidote")
            else:
                damage = []
                for i in self.Trainer_Curr.moveset:
                    if self.Trainer_Curr.moveset[i]["Power"]:
                        damage.append(i)
                if damage:
                    choice = random.randint(0, len(damage)-1)
                    print(f"{self.Trainer_Curr.name.capitalize()} used {damage[choice]}")
                    matchup = asyncio.run(Matchup(self.Trainer_Curr.moveset[damage[choice]]["Type_URL"]))
                    multiplier = 1
                    has_mul_1 = None
                    has_mul_2 = None
                    for i,j in matchup.items():
                        if self.Player_Curr.Type_1 in j:
                            has_mul_1 = i
                        if self.Player_Curr.Type_2 in j:
                            has_mul_2 = i
                    
                    has_mul_1 = self.convert_multipliers(has_mul_1)
                    if self.Trainer_Curr.Type_2:
                        has_mul_2 = self.convert_multipliers(has_mul_2)
                    else:
                        has_mul_2 = 1
                    
                    multiplier *= has_mul_1 * has_mul_2        
                    if multiplier > 1:
                        print("It's Super Effective!")
                    if 0 < multiplier < 1:
                        print("It's not Very Effective")
                    
                    if multiplier != 0:
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
                            self.Player_Curr.life = "Dead"
                            dead = self.Player_Curr
                            self.Player.Dead_Pokemons.append(dead)
                            check = self.check_match()
                            if check:
                                return True
                            else:
                                self.Switch_Pokemons(self.Player)
                    else:
                        print(f"{self.Player_Curr.name} is immune to {damage[choice]}")
                else:
                    print("No damaging Moves, lol betacuck")
                
        if self.Trainer_Curr.Status_condition == "Poisoned" or self.Trainer_Curr.Status_condition == "Burned":
            Status_condition_effect(self.Trainer_Curr)
