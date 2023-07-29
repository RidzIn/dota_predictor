import json
import pandas as pd


def read_heroes(filename="data_processing/data/heroes/heroes.txt"):
    """
    Take txt file of heroes and return set object
    """
    hero_set = set()
    with open(filename, "r") as file:
        for line in file:
            hero_set.add(line.strip())
    return hero_set


def read_winrates(file_name='data_processing/data/winrates/winrates.json'):
    """Return winrates dictionary"""
    f = open(file_name)
    winrates = json.load(f)
    return winrates


def read_xgb_model():
    return pd.read_pickle('data_processing/data/models/xgboost_model.pkl')


def get_feature_vec(winrates: dict, pick_1: list, pick_2: list) -> list:
    """
    Compute the complete feature vector for two Dota 2 picks based on their win rates and synergies.

    Parameters:
        winrates (dict): A dictionary of win rates of every hero against and with each other hero.
        pick_1 (list): The list of the heroes.
        pick_2 (list): The list of the second heroes.

    Returns:
        list: Features for the two picks.(len:80)

    The feature vector is computed by concatenating the following four types of features:
        - Synergy features for pick_1, pick_2 (computed using the `get_synergy_features` function).
        - Duel features for heroes in pick_1 and pick_2 (computed using the `get_duel_features` function).
    """
    pick_1_synergy_features = get_synergy_features(winrates, pick_1)
    pick_2_synergy_features = get_synergy_features(winrates, pick_2)
    pick_1_duel_features, pick_2_duel_features = get_duel_features(
        winrates, pick_1, pick_2
    )

    return (
            pick_1_synergy_features
            + pick_1_duel_features
            + pick_2_synergy_features
            + pick_2_duel_features
    )


def get_synergy_features(winrates: dict, pick: list) -> list:
    """
    Compute the synergy features for a pick based on their win rates with each others.

    Parameters:
        winrates (dict): A dictionary of win rates for heroes with each other.
        pick (list): A list of heroes.

    Returns:
       list: Synergy features for the given heroes.(len:15)

    The synergy features are computed by iterating over each pair of heroes in the list and
    appending their "with" win rate to the feature vector.

    """
    pick_copy = pick[::]
    synergy_features = []
    for h1 in pick:
        for h2 in pick_copy:
            synergy_features.append(winrates[h1][h2]["with_winrate"])
        del pick_copy[0]
    return synergy_features


def get_duel_features(winrates: dict, pick_1: list, pick_2: list) -> tuple:
    """
    Compute the duel features for two lists of Dota 2 heroes based on their win rates.

    Parameters:
        winrates (dict): A dictionary of win rates for pairs of heroes.
        pick_1 (list): A list of hero names for the first pick.
        pick_2 (list): A list of hero names for the second pick.

    Returns:
        tuple: Two lists of duel features, one for each team.(len:50)

    The duel features are computed by iterating over all pairs of heroes from the two picks and
    appending their "against" win rate to the feature vector.

    """
    duel_features1, duel_features2 = [], []
    for h1 in pick_1:
        for h2 in pick_2:
            against_winrate = winrates[h1][h2].get("against_winrate", 0)
            duel_features1.append(against_winrate)
            duel_features2.append(1 - against_winrate)
    return duel_features1, duel_features2


