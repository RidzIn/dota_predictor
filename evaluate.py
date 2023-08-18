import pandas as pd
from tqdm import tqdm

from data_processing.predict import *

valid_df = pd.read_pickle('data_processing/data/datasets/riyadh_RESHAPED.pickle')


def evaluate(df):
    log = []
    for match in tqdm(df):
        pick_1 = match['TEAM_0_HEROES']
        pick_2 = match['TEAM_1_HEROES']

        result = 'pick_1' if match['TEAM_0_WIN'] == 1 else 'pick_2'

        _, prediction = get_prediction(pick_1, pick_2)

        predicted_pick = 'pick_1' if prediction['pick'][0] in pick_1 else 'pick_2'
        is_right = 1 if predicted_pick == result else 0
        scores = prediction['scores']
        log.append({'prediction': is_right, 'scores': scores})
    return log


pick_1 = ['Riki', 'Mars']
pick_2 = ['Mars', 'Riki']

print(pick_1[0] in pick_2)
