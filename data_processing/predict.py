from joblib import load

from data_processing.util import *


from selenium import webdriver
from selenium.webdriver.edge.options import Options

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')

driver = webdriver.Edge(options=options)


def get_nn_pred(winrates, model, pick_1, pick_2):
    """
    Using fine tuned XGBBoost classifier model returns dictionary {pick_1: <probability>, 'pick_2': <probability>}
    """
    vec = get_feature_vec(winrates, pick_1, pick_2)
    pred = model.predict_proba([vec])
    return {"pick_1": round(pred[0][0], 2), "pick_2": round(pred[0][1], 2)}


def get_row_prediction(winrates, xgb, rf, pick_1, pick_2):
    """Return models prediction without any additional  checkers"""
    return {
        "rf":  get_nn_pred(winrates, rf, pick_1, pick_2),
        "xgb": get_nn_pred(winrates, xgb, pick_1, pick_2),
    }


def get_feedback_prediction(
        winrates, rf_feedback, xgb_feedback, rf, xgb, pick_1, pick_2
):
    result = {"rf": 0, "xgb": 0}

    prediction = get_row_prediction(winrates, xgb, rf,  pick_1, pick_2)
    for m in prediction.keys():
        if prediction[m]["pick_1"] > prediction[m]["pick_2"]:
            predicted_pick = pick_1
            unpredicted_pick = pick_2
        else:
            predicted_pick = pick_1
            unpredicted_pick = pick_2

        predicted_winrate = 0
        for hero in predicted_pick:
            if m == "rf":
                predicted_winrate += rf_feedback[hero]["predicted_winrate"]
            else:
                predicted_winrate += xgb_feedback[hero]["predicted_winrate"]

        unpredicted_winrate = 0
        for hero in unpredicted_pick:
            if m == "rf":
                unpredicted_winrate += rf_feedback[hero]["unpredicted_winrate"]
            else:
                unpredicted_winrate += xgb_feedback[hero]["unpredicted_winrate"]

        result[m] = {
            "predicted_winrate": round(predicted_winrate / 5, 2),
            "unpredicted_winrate": round(unpredicted_winrate / 5, 2),
        }
    return result


def get_meta_prediction(pick_1, pick_2):
    """Parse data from OpenDota API and calculate win probability based on recent matches played on this
    heroes by non-professional players"""
    avg_winrates = {}
    for hero in pick_1:
        temp_df = get_hero_matchups(hero, pick_2)
        avg_winrates[hero] = temp_df["winrate"].sum() / 5
    team_1_win_prob = round(sum(avg_winrates.values()) / 5, 3)
    return {"pick_1": team_1_win_prob, "pick_2": 1 - team_1_win_prob}


def get_json(team):
    response = requests.get(f'https://dltv.org/api/v1/teams/{team}/stats')
    return response.json()


def get_decoder(data):
    result = {}
    for _, hero in data['heroes'].items():
        result.update({hero['title']: hero['id']})
    return result


def decode_pick(pick, data):
    decoder = get_decoder(data)
    result = []
    for hero in pick:
        result.append(decoder[hero])
    return result


def reformat_team_name(team: str):
    if team.lower() == 'nigma galaxy':
        return 'nigma'
    if team.lower() == 'level up':
        return 'lvlup'
    return team.lower().replace(' ', '')


def get_personal_pick_winrates(pick, team):
    team = reformat_team_name(team)
    result = {}
    data = get_json(team)
    decoded_pick = decode_pick(pick, data)
    i = 0
    for hero in pick:
        for row in data['stats']:
            try:
                if row['hero_id'] == decoded_pick[i]:
                    if row['maps_total'] >= 3:
                        result.update({hero: round(row['wins_total'] / (row['maps_total'] + 0.0001), 2)})
                    else:
                        result.update({hero: 0.5})
            except KeyError as e:
                pass
        i += 1
    avg_winrate = 0
    team_winrate = round(data['stats'][0]['wins_total'] / (data['stats'][0]['maps_total'] + 0.0001), 2)
    for hero_winrate in result.values():
        avg_winrate += hero_winrate - team_winrate
    result.update({'avg_winrate': round(0.5 + avg_winrate, 2)})
    return result


hyper_params = {
    "rf_row_threshold": 0.65,
    "xgb_row_threshold": 0.80,
    "predicted_feedback_threshold": 0.54,
    "unpredicted_feedback_threshold": 0.46,
    "meta_threshold": 0.51,
}


def get_prediction(pick_1, pick_2, team_1=None, team_2=None):
    scores = 0

    row_prediction = get_row_prediction(winrates, xgb_model, rf_model, pick_1, pick_2)

    predicted_pick = pick_1 if row_prediction["rf"]["pick_1"] > 0.50 else pick_2
    predicted_team = team_1 if row_prediction['rf']['pick_1'] > 0.50 else team_2
    unpredicted_pick = pick_2 if row_prediction["rf"]["pick_1"] > 0.50 else pick_1
    unpredicted_team = team_2 if row_prediction['rf']['pick_1'] > 0.50 else team_1
    predicted_pick_str = (
        "pick_1" if row_prediction["rf"]["pick_1"] > 0.50 else "pick_2"
    )
    unpredicted_pick_str = (
        "pick_2" if row_prediction["rf"]["pick_1"] > 0.50 else "pick_1"
    )

    if (
            row_prediction["rf"]["pick_1"] >= hyper_params["rf_row_threshold"]
            or row_prediction["rf"]["pick_2"] >= hyper_params["rf_row_threshold"]
    ):
        scores += 1

    if (
            row_prediction["xgb"]["pick_1"] >= hyper_params["xgb_row_threshold"]
            or row_prediction["xgb"]["pick_2"] >= hyper_params["xgb_row_threshold"]
    ):
        scores += 1

    feedback_prediction = get_feedback_prediction(
        winrates, rf_feedback, xgb_feedback, rf_model, xgb_model, pick_1, pick_2)

    if (
            feedback_prediction["rf"]["predicted_winrate"]
            >= hyper_params["predicted_feedback_threshold"]
    ):
        scores += 1

    if (
            feedback_prediction["rf"]["unpredicted_winrate"]
            <= hyper_params["unpredicted_feedback_threshold"]
    ):
        scores += 1

    if (
            feedback_prediction["xgb"]["predicted_winrate"]
            >= hyper_params["predicted_feedback_threshold"]
    ):
        scores += 1

    if (
            feedback_prediction["xgb"]["unpredicted_winrate"]
            <= hyper_params["unpredicted_feedback_threshold"]
    ):
        scores += 1

    meta_prediction = get_meta_prediction(predicted_pick, unpredicted_pick)
    if meta_prediction[predicted_pick_str] >= hyper_params["meta_threshold"]:
        scores += 1

    result = "\t\t"
    result += f"{predicted_team} |"
    result += print_pick(predicted_pick)
    result += f"\n\n\t| RF Raw: {row_prediction['rf'][predicted_pick_str]} "
    result += (
        f"\n\n\t| RF Feedback: {feedback_prediction['rf']['predicted_winrate']}"
    )
    result += f"\n\n\t| XGB Raw: {row_prediction['xgb'][predicted_pick_str]:.2f}"
    result += f"\n\n\t| XGB Feedback: {feedback_prediction['xgb']['predicted_winrate']}"
    result += f"\n\n\t| Meta: {meta_prediction[predicted_pick_str]}"
    try:
        result += f"\n\n\t| Personal: {get_personal_pick_winrates(predicted_pick, predicted_team)}"
    except Exception as e:
        pass

    result += "\n\n"
    result += f"{unpredicted_team} |"
    result += print_pick(unpredicted_pick)
    result += f"\n\n\t| RF Raw: {row_prediction['rf'][unpredicted_pick_str]}"
    result += f"\n\n\t| Simple Feedback: {feedback_prediction['rf']['unpredicted_winrate']}"
    result += f"\n\n\t| XGB Raw: {row_prediction['xgb'][unpredicted_pick_str]:.2f}"
    result += (
        f"\n\n\t| XGB Feedback: {feedback_prediction['xgb']['unpredicted_winrate']:.2f}"
    )
    result += f"\n\n\t| Meta: {meta_prediction[unpredicted_pick_str]}"
    try:
        result += f"\n\n\t| Personal: {get_personal_pick_winrates(unpredicted_pick, unpredicted_team)}"
    except Exception as e:
        pass
    result += f"\n\nTotal scores: {scores}/8"
    try:
        if get_personal_pick_winrates(predicted_pick, predicted_team)['avg_winrate'] > \
                get_personal_pick_winrates(unpredicted_pick, unpredicted_team)['avg_winrate']:
            scores += 1
    except Exception as e:
        pass

    return result, {'pick': predicted_pick, 'scores': scores}


def print_pick(pick):
    result = ""
    for hero in pick:
        result += "| " + hero + " "
    result += "|"
    return result


winrates = pd.read_json('data_processing/data/winrates/winrates.json')
rf_feedback = pd.read_json('data_processing/data/models_feedback/rf_model_stat.json')
xgb_feedback = pd.read_json('data_processing/data/models_feedback/xgb_model_stat.json')
xgb_model = load('data_processing/data/models/xgb_boost_model.joblib')
rf_model = load('data_processing/data/models/random_forest_model.joblib')
