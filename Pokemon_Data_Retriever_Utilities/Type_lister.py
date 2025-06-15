def type_lister(data):
    type_info = data["types"]
    pokemon_type = {}
    for i in range(len(type_info)):
        if i == 0:
            pokemon_type["Primary"] = type_info[i]["type"]["name"]
        elif i == 1:
            pokemon_type["Secondary"] = type_info[i]["type"]["name"]
    return pokemon_type
