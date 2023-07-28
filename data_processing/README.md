# Data processing
This package to process data, there are few useful scripts to process data for this project. 

---

## Update winrates
This script is needed to update the winrates of all heroes, then these winrates will be used as a vector representation for the XGB model.

**Usage**


From root folder run command `python main.py update_winrates --file_path <path to your reshasped DataFrame object you got from parser module>`
