import requests

def Growth_rate(name, levels):
    growth_rate = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{name}/")
    signal = False
    while not signal:
        if growth_rate.status_code != 200:
            print("Error occured while getting Growth Rate")
            print("Trying again...")
            print(name)
            name1,name2 = name.split("-")
            growth_rate = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{name1}/")
        else:
            signal = True
    growth = growth_rate.json()
    Url = growth["growth_rate"]['url']
    growth_url = requests.get(Url)
    growth_exp = growth_url.json()
    return growth_exp["levels"][levels-1]["experience"]
