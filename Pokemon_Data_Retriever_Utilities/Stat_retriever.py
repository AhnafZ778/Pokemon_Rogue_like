def stat_lister(data):
    stats = data["stats"]
    pokemon_stats = {}
    for i in range(len(stats)):
        base_stat = stats[i]["base_stat"]
        stat_type = stats[i]["stat"]["name"]
        pokemon_stats[stat_type] = base_stat
    return pokemon_stats

