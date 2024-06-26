from joblib import load

from data_processing.util import *
from parser.parse_match import MatchParser
from parser.util import reshape_pick, reshaped_df, reshape_positions


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


# def get_json(team):
#     response = requests.get(f'https://dltv.org/api/v1/teams/{team}/stats')
#     return response.json()
#
#
# def get_decoder(data):
#     result = {}
#     for _, hero in data['heroes'].items():
#         result.update({hero['title']: hero['id']})
#     return result
#
#
# def decode_pick(pick, data):
#     decoder = get_decoder(data)
#     result = []
#     for hero in pick:
#         result.append(decoder[hero])
#     return result
#
#
# def reformat_team_name(team: str):
#     if team.lower() == 'nigma galaxy':
#         return 'nigma'
#     if team.lower() == 'level up':
#         return 'lvlup'
#     return team.lower().replace(' ', '')
#
#
# def get_personal_pick_winrates(pick, team):
#     team = reformat_team_name(team)
#     result = {}
#     data = get_json(team)
#     decoded_pick = decode_pick(pick, data)
#     i = 0
#     for hero in pick:
#         for row in data['stats']:
#             try:
#                 if row['hero_id'] == decoded_pick[i]:
#                     if row['maps_total'] >= 3:
#                         result.update({hero: round(row['wins_total'] / (row['maps_total'] + 0.0001), 2)})
#                     else:
#                         result.update({hero: 0.5})
#             except KeyError as e:
#                 pass
#         i += 1
#     avg_winrate = 0
#     team_winrate = round(data['stats'][0]['wins_total'] / (data['stats'][0]['maps_total'] + 0.0001), 2)
#     for hero_winrate in result.values():
#         avg_winrate += hero_winrate - team_winrate
#     result.update({'avg_winrate': round(0.5 + avg_winrate, 2)})
#     return result


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

    predicted_pick_str = (
        "pick_1" if row_prediction["rf"]["pick_1"] > 0.50 else "pick_2"
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

    pred_feedback = round(
        (feedback_prediction['rf']['predicted_winrate'] + feedback_prediction['xgb']['predicted_winrate']) / 2, 2)
    unpred_feedback = round(
        (feedback_prediction['rf']['unpredicted_winrate'] + feedback_prediction['xgb']['unpredicted_winrate']) / 2, 2)

    if pred_feedback >= 0.54:
        scores += 1
    if unpred_feedback <= 0.45:
        scores += 1

    # meta_prediction = get_meta_prediction(predicted_pick, unpredicted_pick)
    # if meta_prediction[predicted_pick_str] >= hyper_params["meta_threshold"]:
    #     scores += 1

    pred_dict = {'Random Forest': {'pred': row_prediction['rf'][predicted_pick_str], 'target': 0.65},
                 'XGBoost': {'pred': row_prediction['xgb'][predicted_pick_str], 'target': 0.80},
                 'Predicted Feedback': {'pred': pred_feedback, 'target': 0.54},
                 'Unpredicted Feedback': {'pred': unpred_feedback, 'target': 0.45},
                 #'Meta': {'pred': meta_prediction[predicted_pick_str], 'target': 0.51}
                 }


    predicted_result = "\t\t"
    predicted_result += f"\n\n\t| RF Raw: {row_prediction['rf'][predicted_pick_str]} Target: (0.65<)"
    predicted_result += f"\n\n\t| RF Feedback: {feedback_prediction['rf']['predicted_winrate']}\t:(0.54<)"
    predicted_result += f"\n\n\t| RF Unpredicted Feedback:{feedback_prediction['rf']['unpredicted_winrate']}\t:(0.46>)"

    predicted_result += f"\n\n\t| XGB Raw: {row_prediction['xgb'][predicted_pick_str]:.2f}\t:(0.80<)"
    predicted_result += f"\n\n\t| XGB Feedback: {feedback_prediction['xgb']['predicted_winrate']}\t:(0.54<)"
    predicted_result += f"\n\n\t| XGB Unpredicted Feedback:{feedback_prediction['xgb']['unpredicted_winrate']}\t:(0.46>)"

    # predicted_result += f"\n\n\t| Meta: {meta_prediction[predicted_pick_str]}\t:(0.51<)"

    return {'pred_result': predicted_result, 'scores': scores, 'predicted_pick': predicted_pick,
            'pred_team': predicted_team, 'pred_dict': pred_dict}


def print_pick(pick):
    result = ""
    for hero in pick:
        result += "| " + hero + " "
    result += "|"
    return result


def get_teams(response):
    bottom_span = response.text.find('picks__new-picks')
    top_span = response.text.find('picks__new-plus__placeholder')
    span = response.text[bottom_span:top_span]
    id_1 = span.find('https://dltv.org/teams/')
    team_1 = span[id_1:id_1 + 100].split('"')[0]

    id_2 = span[id_1 + 100:].find('https://dltv.org/teams/')
    team_2 = span[id_1 + 100 + id_2: id_1 + id_2 + 500].split('"')[0]
    team_1 = team_1.split("/")[-1]
    team_2 = team_2.split("/")[-1]
    return {'team_1': team_1, 'team_2': team_2}


def get_data(df, map):
    pick_data_1 = {'side': df.iloc[map]['TEAM_0_SIDE'], 'pick': df.iloc[map]['TEAM_0_HEROES'],
                   'team': df.iloc[map]['TEAM_0_NAME']}

    pick_data_2 = {'side': df.iloc[map]['TEAM_1_SIDE'], 'pick': df.iloc[map]['TEAM_1_HEROES'],
                   'team': df.iloc[map]['TEAM_1_NAME']}
    if df.iloc[map]['TEAM_0_SIDE'] == 'radiant':
        return pick_data_2, pick_data_1
    else:
        return pick_data_1, pick_data_2


def get_df(match_link):
    mp = MatchParser(match_string=match_link)

    match = mp.generate_csv_data_map()
    my_data = []

    match = match.split("\n")
    for j in match:
        if len(j) > 10:
            my_data.append(j)

    columns = [
        "MATCH_ID",
        "MAP",
        "TOURNAMENT",
        "TEAM",
        "SIDE",
        "SCORE",
        "RESULT",
        "DURATION",
        "HERO_1",
        "HERO_2",
        "HERO_3",
        "HERO_4",
        "HERO_5",
    ]

    data = [list(i.replace(", ", "").split(",")) for i in my_data]
    df = pd.DataFrame(data, columns=columns)
    return reshaped_df(reshape_positions(df))


def get_pick_data(bottom_span, response, heroes_list):
    pick_data = {'side': None, 'pick': [], 'team': None}

    pick_raw = response.text[bottom_span: bottom_span + response.text[bottom_span:].find('div class="bans"')]

    pick_data['side'] = 'radiant' if pick_raw.find('radiant') != -1 else 'dire'

    for hero in heroes_list:
        if pick_raw.find(hero) != -1:
            pick_data['pick'].append(hero)
    pick_data['pick'] = list(reshape_pick(pick_data['pick']).values())
    return pick_data


def get_parsed_data(match_link, live=True, map=None):
    if live:
        response = requests.get(match_link)
        teams = get_teams(response)

        dire_span = response.text.find('<div class="picks__new-picks__picks dire">')
        radiant_span = response.text.find('<div class="picks__new-picks__picks radiant">')
        first_span = (dire_span, radiant_span) if dire_span < radiant_span else (radiant_span, dire_span)

        heroes_list = []

        with open('parser/heroes.txt') as heroes:
            for line in heroes:
                heroes_list.append(line.strip())

        temp_1 = get_pick_data(first_span[0], response, heroes_list)
        temp_1['team'] = teams['team_1']
        temp_2 = get_pick_data(first_span[1], response, heroes_list)
        temp_2['team'] = teams['team_2']

        return (temp_2, temp_1) if temp_1['side'] == 'radiant' else (temp_1, temp_2)
    else:
        df = get_df(match_link)
        return get_data(df, map)


winrates = pd.read_json('data_processing/data/winrates/winrates.json')
rf_feedback = pd.read_json('data_processing/data/models_feedback/rf_model_stat.json')
xgb_feedback = pd.read_json('data_processing/data/models_feedback/xgb_model_stat.json')
xgb_model = load('data_processing/data/models/xgb_boost_model.joblib')
rf_model = load('data_processing/data/models/random_forest_model.joblib')
