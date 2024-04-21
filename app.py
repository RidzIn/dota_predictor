import pandas as pd
import streamlit as st
from data_processing.util import (
    read_heroes,
    get_hero_performance,
)
from data_processing.predict import get_prediction, get_parsed_data

st.title("Dota 2 pick predictor")
st.write("----")
"""
## How to use
1. Insert link to the match from the [DLTV](https://dltv.org/)
2. Press **predict** button
3. After this you will see the prediction, at the bottom 
----

"""

def print_pred(data):
    df = pd.DataFrame(data).T
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Model', 'pred': 'Prediction', 'target': 'Target'}, inplace=True)
    return df.style.apply(highlight_cells, axis=1)

def highlight_cells(x):
    if 'Unpredicted Feedback' in x['Model']:
        color = 'background-color: green' if x['Prediction'] < x['Target'] else ''
    else:
        color = 'background-color: green' if x['Prediction'] > x['Target'] else ''
    return [color if col == 'Prediction' else '' for col in x.index]


def print_hero_metric(index):
    st.sidebar.header(match_heroes[index])
    hero_perf = get_hero_performance(
        match_heroes[index],
        temp_dict[0]["pick"],
        temp_dict[1]["pick"],
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

tab1, tab2 = st.tabs(["Insert Link", "Test yourself"])
with tab1:
    """ """

    st.header("Predict")
    """
    ----
    """
    link = st.text_input("**Insert match link from [DLTV.ORG](https://dltv.org//)**")

    if st.button("Predict", key=2):
        temp_dict = get_parsed_data(link)

        pred = get_prediction(temp_dict[0]["pick"],
                              temp_dict[1]["pick"],
                              temp_dict[0]['team'],
                              temp_dict[1]['team'])

        st.header(f"{pred['pred_team']}")
        st.write(f"{pred['predicted_pick']}")
        st.write('----')
        st.dataframe(print_pred(pred['pred_dict']))
        st.write('----')
        st.header(f'Total scores: {pred["scores"]}')
        match_heroes = temp_dict[0]["pick"] + temp_dict[1]["pick"]

        for h in range(len(match_heroes)):
            if h == 0:
                st.sidebar.write("----")
                st.sidebar.title(temp_dict[0]["team"])
                st.sidebar.write("----")
            if h == 5:
                st.sidebar.write("----")
                st.sidebar.title(temp_dict[1]["team"])
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
