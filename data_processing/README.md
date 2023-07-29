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

