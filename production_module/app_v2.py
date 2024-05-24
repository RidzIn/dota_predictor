import json

import pandas as pd
import requests
import streamlit as st

from utils import predict_v2

f = open("../data_processing/data/heroes/heroes_decoder.json")

heroes_id_names = json.load(f)


def get_match_picks(match_id):
    response = requests.get(f'https://api.opendota.com/api/matches/{match_id}')

    radiant_picks = [pick["hero_id"] for pick in response.json()['picks_bans'] if pick["is_pick"] and pick["team"] == 0]
    dire_picks = [pick["hero_id"] for pick in response.json()['picks_bans'] if pick["is_pick"] and pick["team"] == 1]

    radiant_picks_decode = []
    dire_picks_decode = []
    for id in radiant_picks:
        for key, value in heroes_id_names.items():
            if int(key) == int(id):
                radiant_picks_decode.append(value)
                break

    for id in dire_picks:
        for key, value in heroes_id_names.items():
            if int(key) == int(id):
                dire_picks_decode.append(value)
                break

    return {"dire": dire_picks_decode, 'radiant': radiant_picks_decode,
            "dire_team": response.json()['dire_team']['name'], 'radiant_team': response.json()['radiant_team']['name']}


match_id = st.number_input(label="Put match id")

if st.button("Predict", key=2):
    temp_dict = get_match_picks(int(match_id))

    pred = predict_v2(temp_dict["dire"], temp_dict["radiant"])
    pred['dire_team'] = temp_dict['dire_team']
    pred['radiant_team'] = temp_dict['radiant_team']
    st.json(pred)

