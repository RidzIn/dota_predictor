import json

import pandas as pd
from tqdm import tqdm

from data_processing.util import read_heroes

MIN_MATCHUPS = 3


def get_matches_hero_appears(df, hero):
    """Return matches where particular hero appears, uses reshaped DataFrame"""
    condition = df["TEAM_0_HEROES"].apply(lambda x: hero in x) | df[
        "TEAM_1_HEROES"
    ].apply(lambda x: hero in x)
    return df[condition]


def get_matches_hero_with_hero(df, hero_1, hero_2):
    """Return matches where 2 heroes in the same pick, uses reshaped DataFrame"""
    condition = df["TEAM_0_HEROES"].apply(lambda x: hero_1 in x and hero_2 in x) | df[
        "TEAM_1_HEROES"
    ].apply(lambda x: hero_1 in x and hero_2 in x)
    return df[condition]


def get_matches_hero_against_hero(df, hero_1, hero_2):
    """Return matches where 2 heroes in different picks, uses reshaped DataFrame"""
    condition = df["TEAM_0_HEROES"].apply(
        lambda x: hero_1 in x and hero_2 not in x
    ) & df["TEAM_1_HEROES"].apply(lambda x: hero_2 in x and hero_1 not in x) | df[
        "TEAM_0_HEROES"
    ].apply(
        lambda x: hero_2 in x and hero_1 not in x
    ) & df[
        "TEAM_1_HEROES"
    ].apply(
        lambda x: hero_1 in x and hero_2 not in x
    )
    return df[condition]


def get_hero_stat(df, hero_to_calculate, hero_to_filter=None, against=True):
    """Return dictionary with statistic for particular hero with/against, uses reshaped DataFrame
    You can filter DataFrame by hero name, to get stats only among them two.
    """
    if hero_to_filter is not None:
        if against:
            df = get_matches_hero_against_hero(df, hero_to_filter, hero_to_calculate)
        else:
            df = get_matches_hero_with_hero(df, hero_to_filter, hero_to_calculate)

    hero_wins = 0
    hero_total = 0

    condition = df["TEAM_0_HEROES"].apply(lambda x: hero_to_calculate in x)
    temp_df = df[condition]
    if len(temp_df) > 0:
        hero_wins += temp_df["TEAM_0_WIN"].sum()
        hero_total += len(temp_df)

    condition = df["TEAM_1_HEROES"].apply(lambda x: hero_to_calculate in x)
    temp_df = df[condition]
    if len(temp_df) > 0:
        hero_wins += temp_df["TEAM_1_WIN"].sum()
        hero_total += len(temp_df)

    winrate = round(hero_wins / hero_total, 2) if hero_total >= MIN_MATCHUPS else 0.5
    return {
        "total": hero_total,
        "wins": hero_wins,
        "loses": hero_total - hero_wins,
        "winrate": winrate,
    }


def get_full_hero_stat(df, hero_to_calculate):
    """Return dictionary: {HERO: {HERO: {against_winrate: <winrate>, 'with_winrate': <winrate>}, ...}}"""

    def reverse_stat(stat_dict):
        loses = stat_dict["loses"]
        wins = stat_dict["wins"]
        winrate = stat_dict["winrate"]
        stat_dict["loses"] = wins
        stat_dict["wins"] = loses
        stat_dict["winrate"] = round(1 - winrate, 2)
        return stat_dict

    result = {hero_to_calculate: {}}
    heroes = read_heroes()
    for hero in heroes:
        if hero == hero_to_calculate:
            result[hero_to_calculate][hero] = {"against_winrate": 0, "with_winrate": 0}
            result[hero_to_calculate][hero]["against_winrate"] = reverse_stat(
                get_hero_stat(df, hero_to_calculate, against=True)
            )["winrate"]
            result[hero_to_calculate][hero]["with_winrate"] = get_hero_stat(
                df, hero_to_calculate, against=False
            )["winrate"]
        else:
            result[hero_to_calculate][hero] = {"against_winrate": 0, "with_winrate": 0}
            result[hero_to_calculate][hero]["against_winrate"] = get_hero_stat(
                df, hero_to_calculate, hero, against=True
            )["winrate"]
            result[hero_to_calculate][hero]["with_winrate"] = get_hero_stat(
                df, hero_to_calculate, hero, against=False
            )["winrate"]
    return result[hero_to_calculate]


def get_updated_winrates_dict(df):
    """Return full stat among every heroes for provided DataFrame, uses reshaped DataFrame"""
    result = {}
    heroes = read_heroes()
    for hero in tqdm(heroes):
        result[hero] = get_full_hero_stat(df, hero)
    return result


def save_winrates(winrates_dict):
    """Save winrates to 'winrates' folder"""
    with open("data_processing/data/winrates/winrates.json", "w") as outfile:
        json.dump(winrates_dict, outfile)


def update_winrates(file_path="data_processing/data/datasets/tier_1_RESHAPED.pickle"):
    df = pd.read_pickle(file_path)
    save_winrates(get_updated_winrates_dict(df))
