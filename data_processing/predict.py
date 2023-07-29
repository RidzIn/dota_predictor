from data_processing.util import get_feature_vec


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
    return {'pick_1': pred[0][0],
            'pick_2': pred[0][1]}

