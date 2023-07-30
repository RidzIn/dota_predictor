import pickle
import numpy as np
import pandas as pd
import xgboost as xgb
from data_processing.predict import get_simple_pred, get_nn_pred
from data_processing.util import read_winrates, get_feature_vec, read_xgb_model

SIMPLE_THRESHOLD = 0.52
XGB_THRESHOLD = 0.8
train_df = pd.read_pickle('data_processing/data/datasets/tier_1_RESHAPED.pickle')
test_df = pd.read_pickle('data_processing/data/datasets/tier_2_2021.pkl')
valid_df = pd.read_pickle('data_processing/data/datasets/riyadh_RESHAPED.pickle')

winrates = read_winrates()
xgb_classifier = read_xgb_model()


def get_picks_result(df):
    result = []
    for i in range(len(df)):
        result.append({'pick_1': df.iloc[i]['TEAM_0_HEROES'],
                       'pick_2': df.iloc[i]['TEAM_1_HEROES'],
                       'result': df.iloc[i]['TEAM_1_WIN']})
    return result


def get_vector_result(df):
    X, y = [], []
    for i in range(len(df)):
        X.append(get_feature_vec(winrates, df.iloc[i]['TEAM_0_HEROES'], df.iloc[i]['TEAM_1_HEROES']))
        y.append(df.iloc[i]['TEAM_1_WIN'])
    return np.array(X), np.array(y)


def accuracy(df, winrates, simple=True, model=None, threshold=0.51):
    right = 0
    wrong = 0
    unpredicted = 0

    picks_result = get_picks_result(df)
    for i in range(len(picks_result)):
        if simple:
            pred = get_simple_pred(winrates, picks_result[i]['pick_1'], picks_result[i]['pick_2'])
        else:
            pred = get_nn_pred(winrates, model, picks_result[i]['pick_1'], picks_result[i]['pick_2'])

        if pred['pick_2'] > threshold:
            if picks_result[i]['result'] == 1:
                right += 1
            else:
                wrong += 1
        elif pred['pick_1'] > threshold:
            if picks_result[i]['result'] == 0:
                right += 1
            else:
                wrong += 1
        else:
            unpredicted += 1
    return {'unpredicted': unpredicted, 'right': right, 'wrong': wrong,
            'winrate': round(right / (right + wrong + 0.0001), 2),
            'predict_rate': round((len(df) - unpredicted) / len(df), 2)}


def train_xgb_model():
    """
    Train, evaluate and save fine-tuned XGB model into 'models' folder.
    Go to source code to change params, and threshold in case you needed.
    """

    params = {
        'learning_rate': 0.2,
        'n_estimators': 150,
        'max_depth': 3,
        'min_child_weight': 3,
        'subsample': 1,
        'colsample_bytree': 1,
        'gamma': 0,
        'eval_metric': 'logloss',
        'objective': 'binary:logistic'
    }

    X_train, y_train = get_vector_result(train_df)

    xgb_classifier = xgb.XGBClassifier(**params)
    xgb_classifier.fit(X_train, y_train)
    print('\tXGB model:')
    print('Test:', accuracy(test_df, winrates, simple=False, model=xgb_classifier, threshold=XGB_THRESHOLD))
    print('Valid', accuracy(valid_df, winrates, simple=False, model=xgb_classifier, threshold=XGB_THRESHOLD))

    model_file_path = 'data_processing/data/models/xgboost_model.pkl'

    # Save the model to the pickle file
    with open(model_file_path, 'wb') as file:
        pickle.dump(xgb_classifier, file)


def evaluate_models():
    print('Simple model:')
    print('\tTest:', accuracy(test_df, winrates, threshold=SIMPLE_THRESHOLD))
    print('\tValid', accuracy(valid_df, winrates, threshold=SIMPLE_THRESHOLD))

    print('XGB model:')
    print('\tTest:', accuracy(test_df, winrates, simple=False, model=xgb_classifier, threshold=XGB_THRESHOLD))
    print('\tValid', accuracy(valid_df, winrates, simple=False, model=xgb_classifier, threshold=XGB_THRESHOLD))


