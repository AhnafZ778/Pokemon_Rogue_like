from names_generator import generate_name

class Trainer:
    
    def __init__(self):
        random_name = generate_name()
        first, last = random_name.split("_")
        self.trainer_name = first + " " + last
        self.trainer_ID = uuid.uuid1()
        self.pokemon_ID = random.randrange(1, 50, 5)
    def give_Pokemons(self):
        number = random.randint(1,5)
        self.Pokemons = []
        self.Pokemons_reference = []
        for i in range(number):
            pokemon_ID = random.randint(1, 500)
            new_Pokemon = (Pokemon(pokemon_ID))
            self.Pokemons.append(new_Pokemon.name)
            self.Pokemons_reference.append(new_Pokemon)
