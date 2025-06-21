import requests
from collections import defaultdict
# import re
import asyncio
import aiohttp
# import time


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

def move_get(session, info):
    moves = []
    for i in range(len(info["moves"])):
        URL = (info["moves"][i]["move"]["url"])
        moves.append(session.get(URL, ssl=False))
    return moves
async def move_retreiver(name, levels = 5):
    moves_ret = {}
    starting_moveset = {}
    level_storage = defaultdict(list)
    async with aiohttp.ClientSession() as session:
        info = Get_Pokemon_info(name)
        level = []
        for i in range(len(info["moves"])):
            status_effect = ""
            status_chance = 0
            level.append(info["moves"][i]["version_group_details"][0]["level_learned_at"])
        responses = move_get(session, info)
        move_rets = await asyncio.gather(*responses)
        move_ret = []
        for response in move_rets:
            move_ret.append(await response.json())
        for i in range(len(move_ret)):
            moves_ret[move_ret[i]["name"]] = {"Power": move_ret[i]["power"], "Accuracy": move_ret[i]["accuracy"], "PP": move_ret[i]["pp"], "Priority" : move_ret[i]["priority"], "Type" : move_ret[i]["type"]["name"]}
            if not level_storage[level[i]]:
                level_storage[level[i]] = [move_ret[i]["name"]]
            else:
                level_storage[level[i]].append(move_ret[i]["name"])
            if 0 < level[i] < levels and len(starting_moveset) < 4: 
                if(move_ret[i]["meta"]["ailment"]["name"]):
                    status_effect = move_ret[i]["meta"]["ailment"]["name"]
                    status_chance = move_ret[i]["meta"]["ailment_chance"]
                if not move_ret[i]["power"] and move_ret[i]["stat_changes"]:
                    status_effect = move_ret[i]["stat_changes"][0]["stat"]["name"]
                    status_chance = move_ret[i]["stat_changes"][0]["change"]
                    # print(status_effect, status_chance)

                ### Space for working on confusion moves
                
                
                ### End
            
                starting_moveset[move_ret[i]["name"]] = {"Power": move_ret[i]["power"], "Accuracy": move_ret[i]["accuracy"], "PP": move_ret[i]["pp"], "Priority" : move_ret[i]["priority"],"Status_changes": {status_effect: status_chance} }
    return starting_moveset, moves_ret, level_storager"], "Accuracy": move_ret[i]["accuracy"], "PP": move_ret[i]["pp"], "Priority" : move_ret[i]["priority"],"Status_changes": {status_effect: status_chance} }
    return starting_moveset, moves, level_storage
  
