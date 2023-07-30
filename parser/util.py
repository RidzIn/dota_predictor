import json
import os

import pandas as pd
from tqdm import tqdm


def pos_reshape_csv(data_file, is_reshaped=True):
    """
    Read a CSV file, reshape positions in the DataFrame, and save the data.

    Args:
        data_file (str): Path to the input CSV file.
        is_reshaped (bool, optional): Whether to reshape DataFrame or not.

    Returns:
        None (if is_reshaped is False) or str: If is_reshaped is True, returns the path of the
                                               saved pickled DataFrame file.
                                               If is_reshaped is False, no return value.

    Raises:
        FileNotFoundError: If the specified CSV file does not exist.
    """
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"CSV file not found: {data_file}")

    df = pd.read_csv(data_file)
    df = reshape_positions(df)
    if is_reshaped:
        resh_df = reshaped_df(df)
        pickled_file_path = data_file + "_RESHAPED.pickle"
        resh_df.to_pickle(pickled_file_path)
    else:
        csv_file_path = data_file + ".csv"
        df.to_csv(csv_file_path, index=False)


def reshaped_df(df):
    """
    Reshape the input DataFrame to a new DataFrame with specific column structure.

    Args:
        df (pandas.DataFrame): The input DataFrame to be reshaped.

    Returns:
        pandas.DataFrame: The reshaped DataFrame with specific columns.

    Note:
        The input DataFrame should have the following columns:
        - TOURNAMENT
        - TEAM
        - HERO_1, HERO_2, HERO_3, HERO_4, HERO_5
        - SIDE
        - RESULT

        The returned DataFrame will have the following columns:
        - TOURNAMENT
        - TEAM_0_NAME, TEAM_0_HEROES, TEAM_0_SIDE, TEAM_0_WIN
        - TEAM_1_NAME, TEAM_1_HEROES, TEAM_1_SIDE, TEAM_1_WIN
    """
    columns = [
        "TOURNAMENT",
        "TEAM_0_NAME",
        "TEAM_0_HEROES",
        "TEAM_0_SIDE",
        "TEAM_0_WIN",
        "TEAM_1_NAME",
        "TEAM_1_HEROES",
        "TEAM_1_SIDE",
        "TEAM_1_WIN",
    ]

    records = []
    for i in tqdm(range(1, len(df), 2)):
        if df.loc[i - 1, "SIDE"] == "dire":
            record = [
                df.loc[i, "TOURNAMENT"],
                df.loc[i - 1, "TEAM"],
                df.loc[
                    i - 1, ["HERO_1", "HERO_2", "HERO_3", "HERO_4", "HERO_5"]
                ].values.tolist(),
                df.loc[i - 1, "SIDE"],
                1 if df.loc[i - 1, "RESULT"] == "WIN" else 0,
                df.loc[i, "TEAM"],
                df.loc[
                    i, ["HERO_1", "HERO_2", "HERO_3", "HERO_4", "HERO_5"]
                ].values.tolist(),
                df.loc[i, "SIDE"],
                1 if df.loc[i, "RESULT"] == "WIN" else 0,
            ]
        if df.loc[i - 1, "SIDE"] == "radiant":
            record = [
                df.loc[i, "TOURNAMENT"],
                df.loc[i, "TEAM"],
                df.loc[
                    i, ["HERO_1", "HERO_2", "HERO_3", "HERO_4", "HERO_5"]
                ].values.tolist(),
                df.loc[i, "SIDE"],
                1 if df.loc[i, "RESULT"] == "WIN" else 0,
                df.loc[i - 1, "TEAM"],
                df.loc[
                    i - 1, ["HERO_1", "HERO_2", "HERO_3", "HERO_4", "HERO_5"]
                ].values.tolist(),
                df.loc[i - 1, "SIDE"],
                1 if df.loc[i - 1, "RESULT"] == "WIN" else 0,
            ]
        records.append(record)

    return pd.DataFrame(columns=columns, data=records)


def get_heroes_list():
    """
    Read hero names from 'parser/heroes.txt' and return a list of hero names.

    Returns:
        list: A list of hero names read from the file.

    Raises:
        FileNotFoundError: If the 'parser/heroes.txt' file does not exist.
    """
    try:
        with open("parser/heroes.txt", "r") as f:
            lines = f.readlines()
        hero_names = [line.strip() for line in lines]
        return hero_names
    except FileNotFoundError:
        raise FileNotFoundError("The 'parser/heroes.txt' file does not exist.")


def read_heroes_prior():
    """
    Read hero priorities from 'parser/heroes_prior.txt' and return a dictionary
    with hero names as keys and their respective priorities as values.

    Returns:
        dict: A dictionary containing hero names as keys and their priorities as values.

    Raises:
        FileNotFoundError: If the 'parser/heroes_prior.txt' file does not exist.
        json.JSONDecodeError: If there's an issue decoding JSON data from the file.
    """
    try:
        hero_prior_dict = {}
        with open("parser/heroes_prior.txt", "r") as f:
            lines = f.readlines()

        for i in range(len(lines)):
            lines[i] = lines[i].strip()

        for line in lines:
            hero, prior_json = line.split(" | ")
            try:
                hero_prior_dict[hero] = json.loads(prior_json)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON data for hero '{hero}': {str(e)}")

        return hero_prior_dict

    except FileNotFoundError:
        raise FileNotFoundError("The 'parser/heroes_prior.txt' file does not exist.")


def init_hero_pos_priority():
    return {h: [] for h in get_heroes_list()}


def reshape_pick(pick):
    """
    Reshape the provided "pick" list based on hero priorities and create a new dictionary.

    Args:
        pick (list): A list containing hero names in the order they were picked.

    Returns:
        dict: A dictionary with hero positions (1 to 5) as keys and their corresponding names as values.

    Note:
        The hero priorities are obtained from the 'read_heroes_prior' function.
    """
    hero_prior = read_heroes_prior()
    priors_list = []
    hero_dict = {}
    counter = 1
    for i in pick:
        hero_dict[counter] = i
        counter += 1
        priors_list.append(hero_prior[i])
    transposed = list(zip(*priors_list))
    transposed = [list(row) for row in transposed]
    new_hero_dict = {}

    for i in range(len(transposed)):
        counter = 1
        for k in transposed[i]:
            if 1 == k:
                new_hero_dict[1] = hero_dict.get(counter)
                for n in transposed:
                    n[counter - 1] = 0
                break
            counter += 1
        try:
            if new_hero_dict[1] is not None:
                break
        except KeyError:
            continue

    for i in range(len(transposed)):
        counter = 1
        for k in transposed[i]:
            if 2 == k:
                new_hero_dict[2] = hero_dict.get(counter)
                for n in transposed:
                    n[counter - 1] = 0
                break
            counter += 1
        try:
            if new_hero_dict[2] is not None:
                break
        except KeyError:
            continue

    for i in range(len(transposed)):
        counter = 1
        for k in transposed[i]:
            if 3 == k:
                new_hero_dict[3] = hero_dict.get(counter)
                for n in transposed:
                    n[counter - 1] = 0
                break
            counter += 1
        try:
            if new_hero_dict[3] is not None:
                break
        except KeyError:
            continue

    for i in range(len(transposed)):
        counter = 1
        for k in transposed[i]:
            if 4 == k:
                new_hero_dict[4] = hero_dict.get(counter)
                for n in transposed:
                    n[counter - 1] = 0
                break
            counter += 1
        try:
            if new_hero_dict[4] is not None:
                break
        except KeyError:
            continue
    for i in range(len(transposed)):
        counter = 1
        for k in transposed[i]:
            if 5 == k:
                new_hero_dict[5] = hero_dict.get(counter)
                for n in transposed:
                    n[counter - 1] = 0
                break
            counter += 1
        try:
            if new_hero_dict[5] is not None:
                break
        except KeyError:
            continue

    return new_hero_dict


def every_pick_list(df):
    """
    Create a new list containing formatted hero picks for each row in the DataFrame.

    Args:
        df (pandas.DataFrame): Raw DataFrame

    Returns:
        list: A list containing formatted hero picks for each row in the DataFrame.

    Note:
        The DataFrame should have columns 'HERO_1', 'HERO_2', 'HERO_3', 'HERO_4', 'HERO_5'.
        The returned list will contain strings where hero names are joined using the '|' character.
    """
    pick_formatted_list = df[["HERO_1", "HERO_2", "HERO_3", "HERO_4", "HERO_5"]].apply(
        "|".join, axis=1
    )
    return pick_formatted_list.tolist()


def reshape_positions(df):
    """
    Reshape hero positions in the input DataFrame based on their priority picks.

    Args:
        df (pandas.DataFrame): The input DataFrame containing hero picks.

    Returns:
        pandas.DataFrame: The DataFrame with reshaped hero positions.

    Note:
        The DataFrame should have columns 'HERO_1', 'HERO_2', 'HERO_3', 'HERO_4', 'HERO_5'.
        The hero priorities are obtained from the 'reshape_pick' function.
    """
    pick_list = every_pick_list(df)
    new_pos = [reshape_pick(pick.split("|")) for pick in pick_list]

    pos_1 = [i.get(1) for i in new_pos]
    pos_2 = [i.get(2) for i in new_pos]
    pos_3 = [i.get(3) for i in new_pos]
    pos_4 = [i.get(4) for i in new_pos]
    pos_5 = [i.get(5) for i in new_pos]

    df["HERO_1"] = pos_1
    df["HERO_2"] = pos_2
    df["HERO_3"] = pos_3
    df["HERO_4"] = pos_4
    df["HERO_5"] = pos_5

    return df
