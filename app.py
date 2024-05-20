import json

import pandas as pd
import streamlit as st
from data_processing.util import (
    read_heroes,
    get_hero_performance,
)
from data_processing.predict import get_prediction, get_parsed_data
import requests
st.title("Dota 2 pick predictor")
st.write("----")
"""
## How to use
1. Insert link to the match from the [DLTV](https://dltv.org/)
2. Press **predict** button
3. After this you will see the prediction, at the bottom 
----

"""

f = open("data_processing/data/heroes/heroes_decoder.json")
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


def print_pred(data):
    df = pd.DataFrame(data).T
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Model', 'pred': 'Prediction', 'target': 'Target'}, inplace=True)
    return df.style.apply(highlight_cells, axis=1)


def highlight_cells(x):
    if 'Unpredicted Feedback' in x['Model']:
        color = 'background-color: green' if x['Prediction'] <= x['Target'] else ''
    else:
        color = 'background-color: green' if x['Prediction'] >= x['Target'] else ''
    return [color if col == 'Prediction' else '' for col in x.index]


def print_hero_metric(index):
    st.sidebar.header(match_heroes[index])
    hero_perf = get_hero_performance(
        match_heroes[index],
        temp_dict["dire"],
        temp_dict["radiant"],
    )[match_heroes[index]]

    with_perf = round(hero_perf["with"] * 100, 2)
    against_perf = round(hero_perf["against"] * 100, 2)
    total_perf = round(hero_perf["total"] * 100, 2)
    col1, col2, col3 = st.sidebar.columns(3)

    with col1:
        st.metric("**WITH**", with_perf, round(-50 + with_perf, 2))

    with col2:
        st.metric("**AGAINST**", against_perf, round(-50 + against_perf, 2))

    with col3:
        st.metric("**TOTAL**", total_perf, round(-50 + total_perf, 2))


heroes = read_heroes()

""" """

st.header("Predict")
"""
----
"""

tab1, tab2, tab3 = st.tabs(['Link', 'Manual', 'Match_ID'])


with tab1:
    match_id = st.number_input(label="Put match id")


    if st.button("Predict", key=2):
        temp_dict = get_match_picks(int(match_id))

        pred = get_prediction(temp_dict["dire"],
                              temp_dict["radiant"],
                              temp_dict['dire_team'],
                              temp_dict['radiant_team'])


        st.header(f"{pred['pred_team']}")
        st.write(f"{pred['predicted_pick']}")
        st.write('----')
        st.dataframe(print_pred(pred['pred_dict']))
        st.write('----')
        st.header(f'Total scores: {pred["scores"]}')
        match_heroes = temp_dict["dire"] + temp_dict["radiant"]

        for h in range(len(match_heroes)):
            if h == 0:
                st.sidebar.write("----")
                st.sidebar.title(temp_dict["dire_team"])
                st.sidebar.write("----")
            if h == 5:
                st.sidebar.write("----")
                st.sidebar.title(temp_dict["radiant_team"])
                st.sidebar.write("----")
            print_hero_metric(h)

with tab2:
    """
    ## \tSELECT HEROES FOR DIRE TEAM
    """

    dire_1, dire_2, dire_3, dire_4, dire_5 = st.columns(5)

    with dire_1:
        d1 = st.selectbox("Dire Position 1", heroes)

    with dire_2:
        d2 = st.selectbox("Dire Position 2", heroes)

    with dire_3:
        d3 = st.selectbox("Dire Position 3", heroes)

    with dire_4:
        d4 = st.selectbox("Dire Position 4", heroes)

    with dire_5:
        d5 = st.selectbox("Dire Position 5", heroes)

    """
    ## \tSELECT HEROES FOR RADIANT TEAM 
    """

    radiant_1, radiant_2, radiant_3, radiant_4, radiant_5 = st.columns(5)

    with radiant_1:
        r1 = st.selectbox("Radiant Position 1", heroes)

    with radiant_2:
        r2 = st.selectbox("Radiant Position 2", heroes)

    with radiant_3:
        r3 = st.selectbox("Radiant Position 3", heroes)

    with radiant_4:
        r4 = st.selectbox("Radiant Position 4", heroes)

    with radiant_5:
        r5 = st.selectbox("Radiant Position 5", heroes)

    if st.button("Predict", key=1):

        pred = get_prediction([d1, d2, d3, d4, d5], [r1, r2, r3, r4, r5])

        st.write(f"{pred['predicted_pick']}")
        st.write('----')
        st.dataframe(print_pred(pred['pred_dict']))
        st.write('----')
        st.header(f'Total scores: {pred["scores"]}')

        match_heroes = [d1, d2, d3, d4, d5, r1, r2, r3, r4, r5]
        for h in range(len(match_heroes)):
            if h == 0:
                st.sidebar.write("----")
                st.sidebar.title("team_1")
                st.sidebar.write("----")
            if h == 5:
                st.sidebar.write("----")
                st.sidebar.title("team_2")
                st.sidebar.write("----")

with tab3:
    pass