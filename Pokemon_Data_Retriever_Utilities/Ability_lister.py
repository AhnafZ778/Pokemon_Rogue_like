import re 

def ability_list(data):
    abilities = data["abilities"]
    Ability_name = (abilities[0]["ability"]["name"])
    Ability_url = (abilities[0]["ability"]["url"])
    On_Contact = None

    response_new = requests.get(Ability_url)
    response = response_new.json()
    for i,j in response.items():
        if i == "effect_entries":
            n1 = {}
            n1[i] = j
    if re.search("(paraly.*)", n1["effect_entries"][1]["effect"]):
        On_Contact = "Paralysis"
    elif re.search("burn.*", n1["effect_entries"][1]["effect"]):
        On_Contact = "Burn"
    elif re.search("freez.*", n1["effect_entries"][1]["effect"]):
        On_Contact = "Freeze"
    elif re.search("poison.*", n1["effect_entries"][1]["effect"]):
        On_Contact = "Poison"

    return Ability_name, On_Contact if On_Contact else None
