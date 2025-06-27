import random
from pokemon import Pokemon
import requests
import time
start = time.time()
rng = random.randint(1, 840)
response = requests.get(f"https://pokeapi.co/api/v2/location-area/{rng}/")
signal = False
while not signal:
    if response.status_code == 200:
        res = (response.json())
        signal = True
    else:
        print(response.status_code)
        print("error occured while retreiving contacting API")
        print("Trying again...")
        response = requests.get(f"https://pokeapi.co/api/v2/location-area/{rng}/")
location_name = res["location"]["name"]
encounters = res["pokemon_encounters"]
print(f"You just entered {location_name.capitalize()}.")
# print("Possible pokemons are:")
# for i in range(len(res["pokemon_encounters"])):
#     print(res["pokemon_encounters"][i]["pokemon"]["name"])
for i in range(5):
    pokemon_rng = random.randint(1, (len(encounters)-1))
    max_level = (encounters[pokemon_rng]["version_details"][0]["encounter_details"][0]["max_level"])
    min_level = (encounters[pokemon_rng]["version_details"][0]["encounter_details"][0]["min_level"])
    if min_level != max_level:
        level = random.randrange(min_level, max_level)
    else:
        level = min_level
    name = encounters[pokemon_rng]["pokemon"]["name"]
    wild_pokemon = Pokemon(name)
    print(wild_pokemon.moveset)
    print(f"You have encountered a wild level {level} {encounters[pokemon_rng]["pokemon"]["name"].capitalize()}")
