# Data processing
This package to process data, there are few useful scripts to process data for this project. 

---

## Update winrates
This script is needed to update the winrates of all heroes, then these winrates will be used as a vector representation for the XGB model.

**Usage**


From root folder run command `python main.py update_winrates --file_path <path to your reshasped DataFrame object you got from parser module>`

---

## Evaluate models
This script is needed to evaluate 2 models in this project. 
1. Simple model - straight forward algorithm to get prediction
2. XGB boost fine tuned model

**Usage**

From root folder run command `python main.py evaluate models`

---

## Train XGB model
This script is needed to train XGB Model. I have already fine tuned parameters, but you can change them in source code. 

**Usage**

From root folder run command `python main.py train_xgb_model`

---

## Update models feedback
To boost accuracy, I implemented 'model feedback' algorithm.
You need to have valid dataset to process through models, then you get statistic where model were wrong. 

For example: model pretty bad predicts sven games,
so by adding this algorithm prediction will be noticed about this fact, 
and give more accurate result

Go to source code in case you want to change parameters. 

**Usage**

From root folder run command `python main.py update_models_feedback`




