from data_processing.util import *


def get_simple_pred(winrates: dict, pick_1: list, pick_2: list) -> dict:
    """
    Algorithm to get 'simple' prediction, based on calculation winrates of heroes.
    Returns dictionary {pick_1: <probability>, 'pick_2': <probability>}
    """
    vec = get_feature_vec(winrates, pick_1, pick_2)
    pick_1_score = sum(vec[:40])
    pick_2_score = sum(vec[40:])

    return {
        "pick_1": round(pick_1_score / (pick_2_score + pick_1_score), 3),
        "pick_2": round(pick_2_score / (pick_2_score + pick_1_score), 3),
    }


def get_nn_pred(winrates, model, pick_1, pick_2):
    """
    Using fine tuned XGBBoost classifier model returns dictionary {pick_1: <probability>, 'pick_2': <probability>}
    """
    vec = get_feature_vec(winrates, pick_1, pick_2)
    pred = model.predict_proba([vec])
    return {"pick_1": round(pred[0][0], 2), "pick_2": round(pred[0][1], 2)}


def get_row_prediction(winrates, model, pick_1, pick_2):
    """Return models prediction without any additional  checkers"""
    return {
        "simple": get_simple_pred(winrates, pick_1, pick_2),
        "xgb": get_nn_pred(winrates, model, pick_1, pick_2),
    }


def get_feedback_prediction(
    winrates, simple_feedback, xgb_feedback, model, pick_1, pick_2
):
    result = {"simple": 0, "xgb": 0}
    prediction = get_row_prediction(winrates, model, pick_1, pick_2)
    for m in prediction.keys():
        if prediction[m]["pick_1"] > prediction[m]["pick_2"]:
            predicted_pick = pick_1
            unpredicted_pick = pick_2
        else:
            predicted_pick = pick_1
            unpredicted_pick = pick_2

        predicted_winrate = 0
        for hero in predicted_pick:
            if m == "simple":
                predicted_winrate += simple_feedback[hero]["predicted_winrate"]
            else:
                predicted_winrate += xgb_feedback[hero]["predicted_winrate"]

        unpredicted_winrate = 0
        for hero in unpredicted_pick:
            if m == "simple":
                unpredicted_winrate += simple_feedback[hero]["unpredicted_winrate"]
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


hyper_params = {
    "simple_row_threshold": 0.52,
    "xgb_row_threshold": 0.80,
    "predicted_feedback_threshold": 0.55,
    "unpredicted_feedback_threshold": 0.45,
    "meta_threshold": 0.51,
}


def get_prediction(pick_1, pick_2):
    scores = 0

    row_prediction = get_row_prediction(winrates, model, pick_1, pick_2)
    if (
        row_prediction["simple"]["pick_1"] > 0.50 > row_prediction["xgb"]["pick_1"]
        or row_prediction["simple"]["pick_1"] < 0.50 < row_prediction["xgb"]["pick_1"]
    ):
        return "unpredictable"

    predicted_pick = pick_1 if row_prediction["simple"]["pick_1"] > 0.50 else pick_2
    unpredicted_pick = pick_2 if row_prediction["simple"]["pick_1"] > 0.50 else pick_1
    predicted_pick_str = (
        "pick_1" if row_prediction["simple"]["pick_1"] > 0.50 else "pick_2"
    )
    unpredicted_pick_str = (
        "pick_2" if row_prediction["simple"]["pick_1"] > 0.50 else "pick_1"
    )

    if (
        row_prediction["simple"]["pick_1"] >= hyper_params["simple_row_threshold"]
        or row_prediction["simple"]["pick_2"] >= hyper_params["simple_row_threshold"]
    ):
        scores += 1

    if (
        row_prediction["xgb"]["pick_1"] >= hyper_params["xgb_row_threshold"]
        or row_prediction["xgb"]["pick_2"] >= hyper_params["xgb_row_threshold"]
    ):
        scores += 1

    feedback_prediction = get_feedback_prediction(
        winrates, simple_feedback, xgb_feedback, model, pick_1, pick_2
    )

    if (
        feedback_prediction["simple"]["predicted_winrate"]
        >= hyper_params["predicted_feedback_threshold"]
    ):
        scores += 1

    if (
        feedback_prediction["simple"]["unpredicted_winrate"]
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
    result += print_pick(predicted_pick)
    result += f"\n\n\t| Simple Raw: {row_prediction['simple'][predicted_pick_str]} "
    result += (
        f"\n\n\t| Simple Feedback: {feedback_prediction['simple']['predicted_winrate']}"
    )
    result += f"\n\n\t| XGB Raw: {row_prediction['xgb'][predicted_pick_str]:.2f}"
    result += f"\n\n\t| XGB Feedback: {feedback_prediction['xgb']['predicted_winrate']}"
    result += f"\n\n\t| Meta: {meta_prediction[predicted_pick_str]}"
    result += "\n\n"
    result += print_pick(unpredicted_pick)
    result += f"\n\n\t| Simple Raw: {row_prediction['simple'][unpredicted_pick_str]}"
    result += f"\n\n\t| Simple Feedback: {feedback_prediction['simple']['unpredicted_winrate']}"
    result += f"\n\n\t| XGB Raw: {row_prediction['xgb'][unpredicted_pick_str]:.2f}"
    result += (
        f"\n\n\t| XGB Feedback: {feedback_prediction['xgb']['unpredicted_winrate']:.2f}"
    )
    result += f"\n\n\t| Meta: {meta_prediction[unpredicted_pick_str]}"
    result += f"\n\nTotal scores: {scores}/7"

    return result


def print_pick(pick):
    result = ""
    for hero in pick:
        result += "| " + hero + " "
    result += "|"
    return result


winrates = read_winrates()
simple_feedback = read_simple_feedback()
xgb_feedback = read_xgb_feedback()
model = read_xgb_model()
