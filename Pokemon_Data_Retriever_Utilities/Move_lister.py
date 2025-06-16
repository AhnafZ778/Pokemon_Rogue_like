import requests

def Get_Pokemon_info(name):
    PokeUrl = "https://pokeapi.co/api/v2/"
    PokeUrl += "pokemon/"
    PokeUrl += f"{name}"
    response = requests.get(PokeUrl)
    if response.status_code == 200:
        Pokemon_data = response.json()
        return Pokemon_data
    else:
        print("Invalid Pokemon name")

def move_retreiver(Pokemon, levels = 5):
    moves = {}
    starting_moveset = {}
    info = Get_Pokemon_info(Pokemon)
    for i in range(50):
        status_effect = ""
        status_chance = 0
        level = info["moves"][i]["version_group_details"][0]["level_learned_at"]
        URL = (info["moves"][i]["move"]["url"])
        response = requests.get(URL)
        data = response.json()
        moves[data["name"]] = {"Power": data["power"], "Accuracy": data["accuracy"], "PP": data["pp"], "Priority" : data["priority"], "Level": level}
        if 0 < level < levels and len(starting_moveset) < 4: 
            if(data["meta"]["ailment"]["name"]):
                status_effect = data["meta"]["ailment"]["name"]
                status_chance = data["meta"]["ailment_chance"]
        
            starting_moveset[data["name"]] = {"Power": data["power"], "Accuracy": data["accuracy"], "PP": data["pp"], "Priority" : data["priority"], "Level": level, "Status_changes": {status_effect: status_chance} }
    return starting_moveset, moves

move_retreiver("Pikachu")
