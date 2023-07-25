# Parser

Package to parse data from [DLTV.ORG](https://dltv.org/)

## Usage
You have two options
1. Download tournament HTML page 
2. Download particular match HTML page

### Option: Download Tournament
1. Go to [tournament page](https://dltv.org/events/dreamleague-season-20)
2. Download HTML page(use must to select only HTML in file type menu) to **tournament** folder
3. from root folder run command `python main.py read_tournament`
4. The downloaded matches will be stored in the **matches** folder

### Option: Download Match
1. Go to [match page](https://dltv.org/matches/408200)
2. Download HTML page(use must to select only HTML in file type menu)
3. from root folder run command `python main.py read_match --file_name <file_name>`
4. Parsed data will be stored in the **generated_data** folder
---
* <file_name>.csv - raw format csv file
* <file_name>_RESHAPED.pickle - reshaped format DataFrame object(I used pickle because columns of DataFrame contains arrays)
* heroes_prior.txt - contains preferable positions of each hero, used to sort heroes by position in the game. 