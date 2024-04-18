import json
from collections import Counter

from data_processing.predict import get_nn_pred


MEAN_XGB_PREDICTED = 0.55

MEAN_XGB_UNPREDICTED = 0.43

MEAN_SIMPLE_PREDICTED = 0.56

MEAN_SIMPLE_UNPREDICTED = 0.43


def get_model_raw_info(
    df, winrates, model, min_threshold=0.48, max_threshold=0.52
):
    """
    Evaluates the performance of a model on a test dataset and returns a dictionary of hero picks and predictions.

        Args:
            df (pandas.DataFrame): A test dataset with columns 'TEAM_0_HEROES', 'TEAM_1_HEROES', and 'TEAM_1_WIN'.
            winrates (dict): A dictionary of hero winrates.
            model: A trained model for making predictions.
            min_threshold (float): The minimum threshold for a model's win probability prediction to be considered 'sure'.
            max_threshold (float): The maximum threshold for a model's win probability prediction to be considered 'sure'.

        Returns:
            dict: A dictionary containing lists of hero picks and predictions for the test dataset.
            The dictionary has the following keys:
            - predicted_win_heroes: A list of heroes predicted to win.
            - predicted_lose_heroes: A list of heroes predicted to lose.
            - unpredicted_win_heroes: A list of heroes that were not predicted to win but did.
            - unpredicted_lose_heroes: A list of heroes that were not predicted to lose but did.
    """
    sure = 0
    unsure = 0
    prediction_list = []

    predicted_win_heroes = []
    predicted_lose_heroes = []

    unpredicted_win_heroes = []
    unpredicted_lose_heroes = []

    correct = 0
    incorrect = 0

    for i in range(len(df)):
        team_2_win_prob = get_nn_pred(
                winrates,
                model,
                df.iloc[i]["TEAM_0_HEROES"],
                df.iloc[i]["TEAM_1_HEROES"],
            )["pick_2"]

        if team_2_win_prob >= max_threshold or team_2_win_prob <= min_threshold:
            sure += 1

            if team_2_win_prob >= max_threshold and df.iloc[i]["TEAM_1_WIN"] == 1:
                correct += 1
                predicted_win_heroes.extend(df.iloc[i]["TEAM_1_HEROES"])
                unpredicted_lose_heroes.extend(df.iloc[i]["TEAM_0_HEROES"])
                prediction_list.append(1)

            elif team_2_win_prob <= min_threshold and df.iloc[i]["TEAM_1_WIN"] == 0:
                correct += 1
                predicted_win_heroes.extend(df.iloc[i]["TEAM_0_HEROES"])
                unpredicted_lose_heroes.extend(df.iloc[i]["TEAM_1_HEROES"])
                prediction_list.append(1)

            elif team_2_win_prob >= max_threshold and df.iloc[i]["TEAM_1_WIN"] == 0:
                incorrect += 1
                predicted_lose_heroes.extend(df.iloc[i]["TEAM_1_HEROES"])
                unpredicted_win_heroes.extend(df.iloc[i]["TEAM_0_HEROES"])
                prediction_list.append(-1)

            elif team_2_win_prob <= min_threshold and df.iloc[i]["TEAM_1_WIN"] == 1:
                incorrect += 1
                predicted_lose_heroes.extend(df.iloc[i]["TEAM_0_HEROES"])
                unpredicted_win_heroes.extend(df.iloc[i]["TEAM_1_HEROES"])
                prediction_list.append(-1)
        else:
            unsure += 1
            prediction_list.append(0)

    return {
        "predicted_win_heroes": predicted_win_heroes,
        "predicted_lose_heroes": predicted_lose_heroes,
        "unpredicted_win_heroes": unpredicted_win_heroes,
        "unpredicted_lose_heroes": unpredicted_lose_heroes,
    }


def get_model_lists(pred_dict):
    """
    Counts the occurrences of each hero in the predicted win/loss and unpredicted win/loss lists generated by the
    `get_model_raw_info` function.

    Args:
        pred_dict (dict): A dictionary containing the predicted_win_heroes, predicted_lose_heroes,
                          unpredicted_win_heroes, and unpredicted_lose_heroes lists, as generated by the
                          `get_model_raw_info` function.

    Returns:
        A tuple of lists, where the first element is a list of heroes predicted to win, the second element is a list of
        heroes predicted to lose, the third element is a list of heroes with unpredictable outcomes that won, and the
        fourth element is a list of heroes with unpredictable outcomes that lost.
    """
    counters = {}
    for key in pred_dict:
        counters[key] = Counter(pred_dict[key])
    return (
        counters["predicted_win_heroes"],
        counters["predicted_lose_heroes"],
        counters["unpredicted_win_heroes"],
        counters["unpredicted_lose_heroes"],
    )


def get_model_stat_dict(
    df, winrates, model, min_threshold=0.48, max_threshold=0.52, is_simple=True
):
    """
    Generate a dictionary with statistical information about a model's performance.

    Parameters:
        df (pandas.DataFrame): The dataset to test the model on.
        winrates (dict): A dictionary with win rates for each hero combination.
        model: The predictive model to evaluate.
        min_threshold (float): The minimum threshold for the predicted win rate to be considered "sure".
        max_threshold (float): The maximum threshold for the predicted win rate to be considered "sure".
        is_simple (bool): A flag indicating whether the model to evaluate is a simple model or a neural network.

    Returns:
    A dictionary with the following keys:
        - 'predicted_winrate': The average win rate predicted by the model for all matches in the dataset.
        - 'unpredicted_winrate': The average win rate of the matches where the model was not sure about the outcome.
        - 'correct_predictions': The number of matches where the model's prediction was correct.
        - 'incorrect_predictions': The number of matches where the model's prediction was incorrect.
        - 'sure_predictions_ratio': The percentage of matches where the model was sure about the outcome.
        - 'predicted_win_heroes': A list of heroes that the model predicted would win.
        - 'predicted_lose_heroes': A list of heroes that the model predicted would lose.
        - 'unpredicted_win_heroes': A list of heroes from matches where the model was not sure and the team with those heroes won.
        - 'unpredicted_lose_heroes': A list of heroes from matches where the model was not sure and the team with those heroes lost.
    """
    model_raw_info = get_model_raw_info(
        df, winrates, model, min_threshold, max_threshold, is_simple
    )

    model_counts = get_model_lists(model_raw_info)

    return model_stat_dict(*model_counts)


def model_stat_dict(
    predicted_win_heroes,
    predicted_lose_heroes,
    unpredicted_win_heroes,
    unpredicted_lose_heroes,
):
    """
    Generate a dictionary of statistics for each hero in the game.

    Args:
        predicted_win_heroes (dict): A dictionary of the number of times each hero was predicted to win by the model.
        predicted_lose_heroes (dict): A dictionary of the number of times each hero was predicted to lose by the model.
        unpredicted_win_heroes (dict): A dictionary of the number of times each hero won but was not predicted by the model.
        unpredicted_lose_heroes (dict): A dictionary of the number of times each hero lost but was not predicted by the model.

    Returns:
        A dictionary with hero names as keys and a nested dictionary of the following values as values:
            - predicted_wins: the number of times the hero was predicted to win
            - predicted_loses: the number of times the hero was predicted to lose
            - predicted_winrate: the win rate predicted by the model for this hero
            - unpredicted_wins: the number of times the hero won but was not predicted by the model
            - unpredicted_loses: the number of times the hero lost but was not predicted by the model
            - unpredicted_winrate: the actual win rate of the hero when not predicted by the model
    """
    heroes = set(predicted_win_heroes.keys()) | set(predicted_lose_heroes.keys())

    prediction_stat_dict = {}
    for hero in heroes:
        predicted_wins = predicted_win_heroes.get(hero, 0)
        predicted_loses = predicted_lose_heroes.get(hero, 0)
        unpredicted_wins = unpredicted_win_heroes.get(hero, 0)
        unpredicted_loses = unpredicted_lose_heroes.get(hero, 0)

        total_predicted = predicted_wins + predicted_loses
        total_unpredicted = unpredicted_wins + unpredicted_loses

        predicted_winrate = round(predicted_wins / (total_predicted + 0.0001), 2)
        unpredicted_winrate = round(unpredicted_wins / (total_unpredicted + 0.0001), 2)

        prediction_stat_dict[hero] = {
            "predicted_wins": predicted_wins,
            "predicted_loses": predicted_loses,
            "predicted_winrate": predicted_winrate,
            "unpredicted_wins": unpredicted_wins,
            "unpredicted_loses": unpredicted_loses,
            "unpredicted_winrate": unpredicted_winrate,
        }

    return prediction_stat_dict


def show_mean_winrates(prediction_stat_dict):
    """
    Prints the mean predicted and unpredicted winrates for a given prediction_stat_dict.
    """
    temp = get_mean_winrates(prediction_stat_dict)
    print(f"\tMean predicted winrate: {temp[0]}")
    print(f"\tMean unpredicted winrate: {temp[1]}")


def get_mean_winrates(prediction_stat_dict):
    """
    Calculate the mean predicted and unpredicted winrates for all heroes.

    Args:
    - prediction_stat_dict (dict): a dictionary with the following structure:
        {
            hero_1: {
                'predicted_wins': ...,
                'predicted_loses': ...,
                'predicted_winrate': ...,
                'unpredicted_wins': ...,
                'unpredicted_loses': ...,
                'unpredicted_winrate': ...
            },
            hero_2: {
                ...
            },
            ...
        }

    Returns:
    - A tuple of two floats, the mean predicted winrate and the mean unpredicted winrate, rounded to two decimal places.
    """
    winrates = {"predicted_winrate": [], "unpredicted_winrate": []}
    for hero_stats in prediction_stat_dict.values():
        winrates["predicted_winrate"].append(hero_stats["predicted_winrate"])
        winrates["unpredicted_winrate"].append(hero_stats["unpredicted_winrate"])
    predicted_winrate_mean = sum(winrates["predicted_winrate"]) / len(
        winrates["predicted_winrate"]
    )
    unpredicted_winrate_mean = sum(winrates["unpredicted_winrate"]) / len(
        winrates["unpredicted_winrate"]
    )
    return round(predicted_winrate_mean, 2), round(unpredicted_winrate_mean, 2)


def save_model_stat(
    df,
    winrates,
    model,
    file_name,
    min_threshold=0.48,
    max_threshold=0.52,
    is_simple=True,
):
    temp = get_model_stat_dict(
        df, winrates, model, min_threshold, max_threshold, is_simple
    )
    show_mean_winrates(temp)
    with open(f"data_processing/data/models_feedback/{file_name}.json", "w") as outfile:
        json.dump(temp, outfile)


def update_models_feedback(df, winrates, model_1, model_2):
    """Save some king of model feedback into 'data/models_feedback' folder"""
    # test_df = pd.read_pickle("data_processing/data/datasets/tier_2_2021.pkl")
    # winrates = read_winrates()
    # model = read_xgb_model()

    print("XGB model:")
    save_model_stat(
        df,
        winrates,
        model_1,
        "xgb_model_stat",
        min_threshold=0.20,
        max_threshold=0.80,
        is_simple=False,
    )

    print("RF model:")
    save_model_stat(
        df,
        winrates,
        model_2,
        "rf_model_stat",
        min_threshold=0.35,
        max_threshold=0.65,
        is_simple=False,
    )
